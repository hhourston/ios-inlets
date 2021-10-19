# Inlet Charts

This project is intended to update several inlet charts, as well as automate the process for the future.
The charts are visible at

- [Annual averaged deep water properties for inlets](https://www.pac.dfo-mpo.gc.ca/science/oceans/bc-inlets-mer-de-bras-cb/water-prop-eau-eng.html)
- [Long term trends in deep water properties of BC inlets](https://www.pac.dfo-mpo.gc.ca/science/oceans/bc-inlets-mer-de-bras-cb/index-eng.html)

The backing data can be found at [the waterproperties archive](https://www.waterproperties.ca/osd_data_archive/netCDF_Data/) and can be downloaded to `data/` for offline access.

Inlet polygons defined using https://geojson.io

## Tasks

- [.] Reproduce the original graphs
  - [o] Reproduce one graph (Saanich Inlet temperatures)
    - [X] Get all data associated with Saanich Inlet
    - [X] Collect data into depth buckets
    - [X] Plot data as date recorded (x) against temperature (y)
    - [ ] Figure out different sources
      - [ ] Find missing sources
  - [ ] Extend script for salinity/oxidization
  - [ ] Extend script for other inlets
- [ ] Extend graph with new data
- [ ] Automate graph creation
