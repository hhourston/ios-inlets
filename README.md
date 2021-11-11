# Inlet Charts

This project is intended to update several inlet charts, as well as automate the process for the future.
The charts are visible at

- [Annual averaged deep water properties for inlets](https://www.pac.dfo-mpo.gc.ca/science/oceans/bc-inlets-mer-de-bras-cb/water-prop-eau-eng.html)
- [Long term trends in deep water properties of BC inlets](https://www.pac.dfo-mpo.gc.ca/science/oceans/bc-inlets-mer-de-bras-cb/index-eng.html)

The backing data can be found at [the waterproperties archive](https://www.waterproperties.ca/osd_data_archive/netCDF_Data/) and can be downloaded to `data/` for offline access:

    $ wget -m -np --cut-dirs=2 -P data https://www.waterproperties.ca/osd_data_archive/

Inlet polygons defined using https://geojson.io

## Dependencies

This project depends on (at least)

- [poetry](https://python-poetry.org)
- python development headers (python-dev or equivalent)
- pkg-config
- libcairo development headers (libcairo-dev or equivalent)
- gobject-introspection
- libgirepository

Once those are installed, you can run

    $ poetry install --no-dev

to get all the rest of the dependencies. To get dependencies which are useful for development, simply run

    $ poetry install

instead.

## Tasks

- [X] Reproduce the original graphs
  - [X] Reproduce one graph (Saanich Inlet temperatures)
    - [X] Get all data associated with Saanich Inlet
    - [X] Collect data into depth buckets
    - [X] Plot data as date recorded (x) against temperature (y)
    - [X] Figure out different sources
      - [X] Find missing sources
  - [X] Extend script for salinity/oxidization
  - [X] Extend script for other inlets
- [X] Extend graph with new data
- [X] Allow use of location when lat/long are missing
- [ ] Read time despite errors

## Notes

In order to produce a valuable graph, some of the shell files needed to be tweaked in order to be self-consistent.
This is a list of the changes made.

- Changes made directly to data/www.waterproperties.ca/osd_data_archive/UBC/8703/87030005.UBC
-- Modified pad value of salinity to be -9.99 instead of -9.999 since the actual value of the pad was -9.990
