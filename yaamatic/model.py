from dexml import fields
import dexml
import os.path

from . import atmosphere
from . import templates
from .units import U, Quantity

class Model(dexml.Model):
    @classmethod
    def parse(cls, xml):
        self = super().parse(xml)
        self.finalize()
        # FIXME FIXME: Exception handling to add at least some context
        return self

    def finalize(self):
        pass

# FIXME FIXME FIXME: Move the rest out and split it to separate packages
# (aircraft, engine etc.)
class ActionPoint(Model):
    class meta:
        tagname = 'actionpt'

    x = Quantity(unit='m')
    y = Quantity(unit='m')
    z = Quantity(unit='m')

class Control(Model):
    control = fields.String()

class ControlInput(Control):
    class meta:
        tagname = 'control-input'

    axis = fields.String()
    invert = fields.Boolean(default=False)
    split = fields.Boolean(default=False)
    square = fields.Boolean(default=False)
    src0 = fields.Float(required=False)
    src1 = fields.Float(required=False)
    dst0 = fields.Float(required=False)
    dst1 = fields.Float(required=False)

class ControlOutput(Control):
    class meta:
        tagname = 'control-output'

    prop = fields.String()
    side = fields.String(required=False)
    min = fields.Float(required=False)
    max = fields.Float(required=False)

class ControlSpeed(Control):
    class meta:
        tagname = 'control-speed'

    t_transition = Quantity(attrname='transition-time', unit='s')

class Ballast(Model):
    class meta:
        tagname = 'ballast'

    x = Quantity(unit='m')
    y = Quantity(unit='m')
    z = Quantity(unit='m')
    mass = Quantity(unit='lb')

class Engine(Ballast):
    # YASim-compatible properties:

    # FIXME: Share this somehow?
    inputs = fields.Dict(ControlInput, key='control', required=False) # FIXME: default?
    outputs = fields.Dict(ControlOutput, key='control', required=False) # FIXME: can we do them in JSBSim?
    speeds = fields.Dict(ControlSpeed, key='control', required=False)

    # Additional properties:
    name = fields.String(required=False)

    # Processing functionality:
    def is_same(self, other):
        if self.name is not None:
            return self.name == other.name

        for f in self._type_tags:
            if getattr(self, f, None) != getattr(other, f, None):
                return False
        return True

# (κ - 1)/2
_k_1_2 = (atmosphere.kappa - 1)/2
# κ/(κ - 1)
_k_k_1 = atmosphere.kappa/(atmosphere.kappa - 1)

def _pressure_recovery(M0, M2):
    """Intake pressure recovery factor for given Mach number.

    The air entering the compressor has around M0.5 no matter what the
    flight speed. This changes its pressure and since this pressure is
    added to the compressor pressure, it increases the thrust by this
    factor.

    The insetropic deceleration of flow yields pressure change like

    p₂/p₀ = [(κ-1)/2 ⋅ M₀² ⋅ (1 - (M₂/M₀)²) + 1]^(κ/(κ-1))

    which Peter Kämpf kindly provided in http://aviation.stackexchange.com/a/19466/524

    Multiplying to avoid division-by-zero yields:

    p₂/p₀ = [(κ-1)/2 ⋅ (M₀² - M₂²) + 1]^(κ/(κ-1))
    """
    # XXX: Should we also multiply by 1 - 0.075(M₀ - 1)^1.35
    # to account for shock losses as provided in
    # https://www.grc.nasa.gov/www/k-12/airplane/inleth.html
    # ? Note, that at M₀ = 2 the value is still 0.925, only a tiny bit
    # less than 1.
    return (_k_1_2 * (M0**2 - M2**2) + 1) ** _k_k_1

def _pressure_recovery_ratio(M0, M2):
    return _pressure_recovery(M0, M2) / _pressure_recovery(0, M2)

class JetEngine(Model):
    class meta:
        tagname = 'jet'

    _type_tags = ('mass', 'thrust', 'n1_idle', 'n1_max', 'n2_idle', 'n2_max',
            'tsfc', 'egt', 'epr', 'v_ex', 't_spool', 'bypassratio')

    name = fields.String(required=False)
    # YASim-compatible properties:

    thrust = Quantity(unit='lbf', required=False)
    #afterburner = Quantity(unit='lbf', required=False) # TODO: not supported yet
    rotate = Quantity(default='0 deg')
    n1_idle = fields.Float(attrname='n1-idle', default=55.0)
    n1_max = fields.Float(attrname='n1-max', default=102.0)
    n2_idle = fields.Float(attrname='n2-idle', default=73.0)
    n2_max = fields.Float(attrname='n2-max', default=103.0)
    tsfc = Quantity(default='0.8 lb/h/lbf')
    egt = Quantity(default='1050 K')
    epr = fields.Float(default=3.0)
    v_ex = Quantity(attrname='exhaust-speed', unit='kt', required=False)
    t_spool = Quantity(attrname='spool-time', default='8 s')

    actionpt = fields.Model(ActionPoint, required=False)

    # Additional properties:
    bypassratio = fields.Float(default=0.0)
    flat_temp = Quantity(attrname='flat-to-temp', unit='degC', required=False)
    flat_alt = Quantity(attrname='flat-to-alt', unit='ft', required=False)

    # Alternate properties:
    # NOTE: e.g. GNex list mass flow rate and it should be possible to
    # calculate v_ex from that

    class Cruise(Model):
        class meta:
            tagname = 'cruise'

        thrust = Quantity(unit='lbf')
        alt = Quantity(default='35000 ft')
        mach = fields.Float(required=False)
        speed = Quantity(unit='knot', required=False)
        throttle = fields.Float(default=1.0)

        def get_mach(self):
            if self.mach is None:
                self.mach = atmosphere.machFromSpd(self.speed,
                        atmosphere.getStdTemperature(self.alt))
            return self.mach

        def getTas(self):
            if self.speed is None:
                self.speed = atmosphere.spdFromMach(self.mach,
                        atmosphere.getStdTemperature(self.alt))
            return self.speed

    cruise = fields.Model(Cruise, required=False)

    # Processing functionality:
    def __eq__(self, other):
        if self.name == other.name:
            return True
        else:
            return self.thrust == other.thrust and all(
                    # FIXME: check that the attribute is not specified in
                    # other, even if it gets value from default
                    (getattr(other, a) is None or getattr(self, a) == getattr(other, a)
                        for a in ('n1_idle', 'n1_max', 'n2_idle', 'n2_max',
                            'tsfc', 'egt', 'epr', 'v_ex', 't_spool',
                            'bypassratio', 'flat_temp', 'flat_alt')))

    def _rho_ref(self):
        """Density for which the nominal thrust applies."""
        if self.flat_temp is not None:
            return atmosphere.calcDensity(
                    atmosphere.getStdPressure(0 * U.ft), self.flat_temp)
        elif self.flat_alt is not None:
            return atmosphere.getStdDensity(self.flat_alt)
        else:
            return atmosphere.getStdDensity(0 * U.ft)

    def _thrust_ratio(self, M0, alt, M2, v_ex):
        """Ratio of thrust at given parameters to static thrust.

        :M0: is free stream Mach number.
        :alt: is altitude.
        :M2: is the Mach number at compressor face.
        :v_ex: is the (effective) exhaust velocity.

        See http://aviation.stackexchange.com/a/19466/524
        """
        # Pressure recovery ratio:
        prr = _pressure_recovery_ratio(M0, M2)

        # Density for which the nominal thrust applies if the engine is flat-rated:
        rho_ref = self._rho_ref()
        rho = atmosphere.getStdDensity(alt)

        # Stream speed
        v_0 = atmosphere.spdFromMach(M0, atmosphere.getStdTemperature(alt))

        r = prr * (rho/rho_ref) * (v_ex - v_0)/v_ex

        return r

    def get_v_ex(self):
        if self.v_ex is None:
            if self.cruise is not None:
                M0 = self.cruise.get_mach()
                prr = _pressure_recovery_ratio(M0, 0.5)
                rho_ref = self._rho_ref()
                rho = atmosphere.getStdDensity(self.cruise.alt)
                v0 = self.cruise.getTas()
                r = float(self.cruise.thrust / self.cruise.throttle / self.thrust)
                print('prr={}, rho={:~C}, rho_ref={:~C}, M₀={}, v₀={:~C}, r={}'.format(
                    prr, rho, rho_ref, M0, v0.to_base_units(), r))#DEBUG#
                print('prr * (rho/rho_ref) = {:~C}'.format(prr * (rho/rho_ref)))
                # r = prr * (rho/rho_ref) * (v_ex - v0)/v_ex
                # r = prr * rho/rho_ref * (1 - v0/v_ex)
                # r * rho_ref / (rho * prr) = 1 - v0/v_ex
                # v0/v_ex = 1 - r * rho_ref / (rho * prr)
                # v0/v_ex = (prr * rho - r * rho_ref)/(prr * rho)
                self.v_ex = v0 * prr * rho / (prr * rho - r * rho_ref)
            else:
                print('Using default v_ex')#DEBUG#
                # FIXME: bypass-ratio-dependent
                self.v_ex = U('1555 kt')
            print('v_ex = {:~C}'.format(self.v_ex.to_base_units()))#DEBUG#
        return self.v_ex

    def idle_thrust_table(self, M, alt):
        # XXX: Very wild guesses: 0.1 thrust, M₂ = 0.2 because the danger
        # area is about 2.5 times smaller and 1/3 v_ex, because square root
        # of 10 because 1/10 would be too little (the exhaust speed is still
        # well above 45 m/s).
        return 0.1 * float(self._thrust_ratio(M, alt * U.ft, 0.2,
            self.get_v_ex() / 3))

    def dry_thrust_table(self, M, alt):
        # XXX: 0.5, a Pischweitz's constant from http://aviation.stackexchange.com/a/19466/524
        return float(self._thrust_ratio(M, alt * U.ft, 0.5, self.get_v_ex()))

    def generate(self, outdir):
        outf = os.path.join(outdir, self.name + '.xml')
        tmpl = 'turbine_engine.genshi' # XXX: Allow configuration
        
        templates.generate(tmpl, outf,
            self.__dict__,
            {
                'idle_thrust_table': self.idle_thrust_table,
                'dry_thrust_table': self.dry_thrust_table,
                })

class Airplane(Model):
    class meta:
        tagname = 'airplane'

    # Mass is not used _yet_
    mass = Quantity(unit='lb', required=False)

    # Stupid in yasim, unused here so far
    version = fields.String(required=False)

    # TODO: approach
    # TODO: cruise
    # TODO: possibly other performance restrictions

    # TODO: cockpit: is it useful? the view is defined elsewhere anyway

    # TODO: fuselage
    # TODO: wing
    # TODO: hstab
    # TODO: vstab
    # TODO: mstab

    # TODO: thrusters
    jets = fields.List(JetEngine)
    # TODO: propeller

    # TODO: gear
    # TODO: launchbar

    # TODO: tank

    # TODO: ballast
    # TODO: weight

    # TODO: hitch

    # Processing functionality:
    def engines_to_generte(self):
        def _engs(list_, name):
            n = 1
            for i in range(0, len(list_)):
                e = list_[i]
                for f in list_[0:i]:
                    if e == f:
                        if e.name is None:
                            e.name = f.name
                        break
                else:
                    if e.name is None:
                        e.name = name + str(n)
                        n = n + 1
                    yield e

        yield from _engs(self.jets, 'turbine')

