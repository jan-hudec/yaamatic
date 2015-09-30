=====================
Yet Another AeroMATIC
=====================

----------------------------------------------------------------------
Tool for converting Yasim(-like) flight dynamics models to JSBSim ones
----------------------------------------------------------------------

When creating models for FlightGear, you can choose from two physics
engines—Yasim and JSBSim. JSBSim takes a set of functions that simply
define arbitrary dynamics model, which allows fine-tuning the
behaviour, but requires a lot of data that are hard to derive if you
don't have wind tunnel or at least CFD data. On the other hand Yasim
takes dimensions and some elementary performance data and
guesstimates all the values, but the result can't be tweaked and
any effect it fails to simulate can only be added by modifying
the engine.

So this tool tries to replicate the guesstimation done by Yasim, but
instead of running the result directly inside FlightGear it produces
JSBSim model definition that can be tweaked and have additional
effects added by post-processing or manually.

.. FIXME: Add documentation...
