import argparse
import datetime

import numpy as np

import inlets
import itertools
import matplotlib
import matplotlib.pyplot as plt
import numpy
from numpy.polynomial import polynomial
import os
import scipy.optimize
from typing import Dict, List
import utils

END = datetime.datetime.now()
INLET_LINES = ["m-s", "y-d", "k-o", "c-^", "b-d", "g-s", "r-s", "m-d"]
FIGURE_PATH_BASE = "figures"


###################
# Utility functions
###################


def figure_path(filename: str):
    return os.path.join(FIGURE_PATH_BASE, filename)


def ensure_figure_path():
    try:
        os.mkdir(FIGURE_PATH_BASE)
    except FileExistsError:
        # ignore errors related to path existing
        pass


def bins(min_val, max_val):
    # add 1 to cover matplotlib expecting e.g. [1,2),..,[11,12),[12,13],
    # and 1 for range not including the last value
    return range(min_val, max_val+2)


########################
# Single inlet functions
########################


def chart_deep_data(inlet: inlets.Inlet, limits: List[float], data_fn):
    # produce a matplotlib chart, which can be shown or saved at the upper level
    plt.clf()
    shallow_time, shallow_data = data_fn(inlet, inlets.Category.DEEP)
    middle_time, middle_data = data_fn(inlet, inlets.Category.DEEPER)
    deep_time, deep_data = data_fn(inlet, inlets.Category.DEEPEST)
    if len(limits) > 1:
        shallow_time, shallow_data = zip(
            *[
                [t, d]
                for t, d in zip(shallow_time, shallow_data)
                if limits[0] < d < limits[1]
            ]
        )
        middle_time, middle_data = zip(
            *[
                [t, d]
                for t, d in zip(middle_time, middle_data)
                if limits[0] < d < limits[1]
            ]
        )
        deep_time, deep_data = zip(
            *[[t, d] for t, d in zip(deep_time, deep_data) if limits[0] < d < limits[1]]
        )
    plt.plot(
        shallow_time,
        shallow_data,
        "xg",
        label=utils.label_from_bounds(*inlet.deep_bounds),
    )
    plt.plot(
        middle_time,
        middle_data,
        "+m",
        label=utils.label_from_bounds(*inlet.deeper_bounds),
    )
    plt.plot(
        deep_time,
        deep_data,
        "xb",
        label=utils.label_from_bounds(*inlet.deepest_bounds)
    )
    plt.legend()


def chart_surface_data(inlet: inlets.Inlet, limits: List[float], data_fn):
    plt.clf()
    surface_time, surface_data = data_fn(inlet, inlets.Category.SURFACE)
    shallow_time, shallow_data = data_fn(inlet, inlets.Category.SHALLOW)
    if len(limits) > 1:
        surface_time, surface_data = zip(
            *[
                [t, d]
                for t, d in zip(surface_time, surface_data)
                if limits[0] < d < limits[1]
            ]
        )
        shallow_time, shallow_data = zip(
            *[
                [t, d]
                for t, d in zip(shallow_time, shallow_data)
                if limits[0] < d < limits[1]
            ]
        )
    plt.plot(
        surface_time,
        surface_data,
        "xg",
        label=utils.label_from_bounds(*inlet.surface_bounds),
    )
    if inlet.shallow_bounds is not None:
        plt.plot(
            shallow_time,
            shallow_data,
            "+m",
            label=utils.label_from_bounds(*inlet.shallow_bounds),
        )
    plt.legend()


def chart_surface_and_deep(inlet: inlets.Inlet, limits: List[float], data_fn):
    # Copied from chart_surface_data() and chart_deep_data()
    # data_fn(inlet, bucket): inlet.get_temperature_data(
    #         bucket, before=END, do_average=use_averages
    #     )
    plt.clf()
    surface_time, surface_data = data_fn(inlet, inlets.Category.SURFACE)
    # USED_DEEP Category includes DEEP, DEEPER and DEEPEST, which is
    # what we want
    deep_time, deep_data = data_fn(inlet, inlets.Category.USED_DEEP)

    if len(limits) > 1:
        surface_time, surface_data = zip(
            *[
                [t, d]
                for t, d in zip(surface_time, surface_data)
                if limits[0] < d < limits[1]
            ]
        )
        deep_time, deep_data = zip(
            *[
                [t, d]
                for t, d in zip(deep_time, deep_data)
                if limits[0] < d < limits[1]
            ]
        )
    plt.plot(
        surface_time,
        surface_data,
        "xb",
        label=utils.label_from_bounds(*inlet.surface_bounds),
    )
    plt.plot(
        deep_time,
        deep_data,
        "+m",
        label=utils.label_from_bounds(
            inlet.deep_bounds[0], inlet.deepest_bounds[1]),
    )
    # Run a straight line through the deep T data
    # Compute the best-fit line
    # TODO fix x_values so it has the same uneven spacing as deep_time
    # Convert deep_time to seconds since [1970]
    # x_values = np.linspace(0, 1, len(deep_time))
    deep_time_arr = np.array([*deep_time])
    x_values = (deep_time_arr - np.min(deep_time_arr)) / datetime.timedelta(days=1)
    x_values_sorted = sorted(x_values)
    deep_data_sorted = [
        i for _, i in sorted(zip(x_values, deep_data))
    ]
    coeffs = np.polyfit(x_values_sorted, deep_data_sorted, 1)
    fit_eqn = np.poly1d(coeffs)
    y_hat_sorted = fit_eqn(x_values_sorted)
    plt.plot(sorted(deep_time), y_hat_sorted, c='r')

    plt.legend()


def chart_temperatures(
    inlet: inlets.Inlet, limits: Dict[str, List[float]], use_averages: bool
):
    average = "-average" if use_averages else ""
    ylabel = "Temperature (C)"
    data_fn = lambda inlet, bucket: inlet.get_temperature_data(
        bucket, before=END, do_average=use_averages
    )

    chart_deep_data(inlet, limits["deep"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Deep Water Temperature")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-deep-temperature{average}.png")
    )

    chart_surface_data(inlet, limits["surface"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Surface Water Temperature")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-surface-temperature{average}.png")
    )


def chart_temperatures_surface_deep(
    inlet: inlets.Inlet, limits: Dict[str, List[float]], use_averages: bool
):
    average = "-average" if use_averages else ""
    ylabel = "Temperature (C)"
    data_fn = lambda inlet, bucket: inlet.get_temperature_data(
        bucket, before=END, do_average=use_averages
    )
    # TODO change limits?
    chart_surface_and_deep(inlet, limits["surface"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Surface and Deep Water Temperature")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-surface-deep-temperature{average}.png")
    )


def chart_salinities(
    inlet: inlets.Inlet, limits: Dict[str, List[float]], use_averages: bool
):
    average = "-average" if use_averages else ""
    ylabel = "Salinity (PSU)"
    data_fn = lambda inlet, bucket: inlet.get_salinity_data(
        bucket, before=END, do_average=use_averages
    )

    chart_deep_data(inlet, limits["deep"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Deep Water Salinity")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-deep-salinity{average}.png")
    )

    chart_surface_data(inlet, limits["surface"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Surface Water Salinity")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-surface-salinity{average}.png")
    )


def chart_oxygen_data(
    inlet: inlets.Inlet, limits: Dict[str, List[float]], use_averages: bool
):
    average = "-average" if use_averages else ""
    ylabel = "DO (ml/l)"
    data_fn = lambda inlet, bucket: inlet.get_oxygen_data(
        bucket, before=END, do_average=use_averages
    )

    chart_deep_data(inlet, limits["deep"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Deep Water Dissolved Oxygen")
    plt.savefig(figure_path(f"{utils.normalize(inlet.name)}-deep-oxygen{average}.png"))

    chart_surface_data(inlet, limits["surface"], data_fn)
    plt.ylabel(ylabel)
    plt.title(f"{inlet.name} Surface Water Dissolved Oxygen")
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-surface-oxygen{average}.png")
    )


def chart_stations(
    inlet: inlets.Inlet, _limits: Dict[str, List[float]], _use_averages: bool
):
    # `limits` and `use_averages` are only present to conform to expected function type
    del _limits, _use_averages
    plt.clf()
    data = []
    for year, stations in inlet.get_station_data(before=END).items():
        data.extend([year for _ in range(len(stations))])
    plt.hist(data, bins=bins(min(data), max(data)), align="left", label=f"Number of files {len(data)}")
    plt.ylabel("Number of Stations")
    plt.legend()
    plt.title(f"{inlet.name} Sampling History")
    plt.savefig(figure_path(f"{utils.normalize(inlet.name)}-samples.png"))


def do_chart(
    inlet: inlets.Inlet,
    kind: str,
    use_limits: bool,
    chart_fn,
    use_averages: bool,
):
    averaging = " averages" if use_averages else ""
    print(f"Producing {kind}{averaging} plot for {inlet.name}")
    chart_fn(
        inlet,
        inlet.limits[kind]
        if use_limits and kind in inlet.limits
        else {"deep": [], "surface": []},
        use_averages,
    )


#####################
# All inlet functions
#####################


def chart_all_data(times, data, label=""):
    plt.scatter(times, data, label=label)


def bounds_label(inlet, bucket):
    bounds_name = bucket.lower() + "_bounds"
    bounds = getattr(inlet, bounds_name)
    label = inlet.name
    if bounds[1] is None:
        label += f" >{bounds[0]}"
    else:
        label += f" {bounds[0]}-{bounds[1]}"
    return label


def chart_all_temperature(inlet, bucket):
    label = bounds_label(inlet, bucket)
    chart_all_data(
        *inlet.get_temperature_data(bucket, before=END, do_average=True), label=label
    )
    plt.ylabel("Temperature (C)")


def chart_all_salinity(inlet, bucket):
    label = bounds_label(inlet, bucket)
    chart_all_data(
        *inlet.get_salinity_data(bucket, before=END, do_average=True), label=label
    )
    plt.ylabel("Salinity (PSU)")


def chart_all_oxygen(inlet, bucket):
    label = bounds_label(inlet, bucket)
    chart_all_data(
        *inlet.get_oxygen_data(bucket, before=END, do_average=True), label=label
    )
    plt.ylabel("DO (ml/l)")


def do_chart_all(inlet_list, kind, bucket, chart_all_fn):
    print(f"Producing {kind} plot for {bucket}")
    plt.clf()
    for inlet in inlet_list:
        chart_all_fn(inlet, bucket)
    names = "-".join(utils.normalize(inlet.name) for inlet in inlet_list)
    bounds_name = bucket.lower() + "_bounds"
    lowest = min(getattr(inlet, bounds_name)[0] for inlet in inlet_list)
    highest = max(
        getattr(inlet, bounds_name)[1]
        if getattr(inlet, bounds_name)[1] is not None
        else 0
        for inlet in inlet_list
    )
    if highest < lowest:
        plt.title(f"{kind.capitalize()} comparison below {lowest}m")
        bounds = f"{lowest}-bottom"
    else:
        plt.title(f"{kind.capitalize()} comparison from {lowest}m to {highest}m")
        bounds = f"{lowest}-{highest}"
    plt.legend()
    plt.savefig(figure_path(f"{bounds}-{kind}-{names}.png"))


############################
# Annual averaging functions
############################


def do_annual_work(inlet_list, data_fn, averaging_fn, limit_fn):
    plt.clf()
    for inlet, line_style in zip(inlet_list, INLET_LINES):
        limits = limit_fn(inlet)
        totals = {}
        times, data = data_fn(inlet)
        for time, datum in zip(times, data):
            if len(limits) > 0 and not (limits[0] < datum < limits[1]):
                continue
            utils.update_totals(totals, time.year, datum)

        averages = averaging_fn(totals, data)
        years, values = zip(*sorted(averages.items(), key=lambda item: item[0]))
        plt.plot(years, values, line_style, label=inlet.name)

    plt.legend()


def do_annual_work_parts(
        inlet_list, data_fn, averaging_fn, y_label, title, limit_fn
):
    areas = set(inlet.area for inlet in inlet_list)
    for area in areas:
        do_annual_work(
            [inlet for inlet in inlet_list if inlet.area == area],
            data_fn,
            averaging_fn,
            limit_fn,
        )
        plt.ylabel(y_label)
        plt.title(f"{title} - {area}")
        plt.savefig(
            figure_path(f"{utils.normalize(title)}-{utils.normalize(area)}.png")
        )


def annual_averaging(totals, _data):
    del _data
    return {y: t / n for y, (t, n) in totals.items()}


def anomalies_averaging(totals, data):
    avg = sum(data) / len(data)
    avgs = annual_averaging(totals, data)
    return {y: a - avg for y, a in avgs.items()}


def chart_anomalies(
    inlet_list: List[inlets.Inlet], data_fn, y_label, title, use_limits
):
    do_annual_work_parts(
        inlet_list, data_fn, anomalies_averaging, y_label, title, use_limits
    )


def chart_temperature_anomalies(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing temperature anomaly plots")
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Temperature (C)",
        "Deep Water Temperature Anomalies",
        lambda inlet: inlet.limits["temperature"]["deep"]
        if use_limits and "temperature" in inlet.limits
        else [],
    )
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Temperature (C)",
        "Surface Water Temperature Anomalies",
        lambda inlet: inlet.limits["temperature"]["surface"]
        if use_limits and "temperature" in inlet.limits
        else [],
    )


def do_annual_work_single(
        inlet, data_fn, averaging_fn, limit_fn, title, y_label, category_dict
):
    # Plot data from a single inlet using depth categories defined in
    # category_dict (a dictionary)
    # averaging_fn: either annual_averaging() or anomalies_averaging()
    plt.clf()
    for key, line_style in zip(
            category_dict.keys(), INLET_LINES[:len(category_dict)]
    ):
        depth_limit, category = key, category_dict[key]
        limits = limit_fn(inlet, depth_limit)
        print('limits:', limits)
        totals = {}
        times, data = data_fn(inlet, category)
        print('times:', times)
        print('data:', data)

        for time, datum in zip(times, data):
            if len(limits) > 0 and not (limits[0] < datum < limits[1]):
                continue
            utils.update_totals(totals, time.year, datum)

        averages = averaging_fn(totals, data)
        print('averages:', averages)
        years, values = zip(*sorted(averages.items(), key=lambda item: item[0]))

        # Update label to depth bucket
        if key == 'surface':
            label = utils.label_from_bounds(*inlet.surface_bounds)
        elif key == 'deep':
            label = utils.label_from_bounds(
                inlet.deep_bounds[0], inlet.deepest_bounds[1])
        plt.plot(years, values, line_style, label=label)

    plt.legend()

    # do_annual_work_parts()
    plt.ylabel(y_label)
    plt.title(title)
    plt.savefig(
        figure_path(f"{utils.normalize(title)}.png")
    )
    return


def chart_temperature_anomalies_single(
        inlet_list: List[inlets.Inlet], use_limits: bool
):
    # Plot annual surface and deep anomalies on the same plot
    # for just a single inlet?
    print("Producing temperature anomaly plots for surface and deep")
    data_fn_modified = lambda inlet, category: inlet.get_temperature_data(
            category, do_average=True, before=END
        )
    limit_fn_modified = lambda inlet, depth: inlet.limits["temperature"][
        depth] if use_limits and "temperature" in inlet.limits else []

    category_dict = {'surface': inlets.Category.SURFACE,
                     'deep': inlets.Category.USED_DEEP}

    y_label = "Temperature (C)"

    # Probably don't need to write a chart_anomalies_single() function
    # chart_anomalies(data_fn=lambda inlet:inlet.get_temperature_data)
    # params: inlet_list, data_fn, anomalies_averaging, y_label, title, use_limits

    # do_annual_work_parts(data_fn, averaging_fn=anomalies_averaging)
    # params: inlet_list, data_fn, averaging_fn, y_label, title, limit_fn

    # for area in areas, do_annual_work(inlet_list, data_fn, averaging_fn)
    # perform the averaging, plot all inlets data in selected area
    # --------------------------------------------------------------------

    # do_annual work()
    for inlet_obj in inlet_list:
        title = "{} Surface and Deep Water Temperature Anomalies".format(
            inlet_obj.name)
        do_annual_work_single(
            inlet_obj, data_fn_modified, anomalies_averaging, limit_fn_modified,
            title, y_label, category_dict
        )
    return


def chart_salinity_anomalies(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing salinity anomaly plots")
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Salinity (PSU)",
        "Deep Water Salinity Anomalies",
        lambda inlet: inlet.limits["salinity"]["deep"]
        if use_limits and "salinity" in inlet.limits
        else [],
    )
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Salinity (PSU)",
        "Surface Water Salinity Anomalies",
        lambda inlet: inlet.limits["salinity"]["surface"]
        if use_limits and "salinity" in inlet.limits
        else [],
    )


def chart_oxygen_anomalies(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing oxygen anomaly plot")
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Oxygen (mL/L)",
        "Deep Water Dissolved Oxygen Anomalies",
        lambda inlet: inlet.limits["oxygen"]["deep"]
        if use_limits and "oxygen" in inlet.limits
        else [],
    )
    chart_anomalies(
        inlet_list,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Oxygen (mL/L)",
        "Surface Water Dissolved Oxygen Anomalies",
        lambda inlet: inlet.limits["oxygen"]["surface"]
        if use_limits and "oxygen" in inlet.limits
        else [],
    )


def do_chart_annual_averages(
    inlet_list: List[inlets.Inlet], data_fn, y_label, title, limit_fn
):
    do_annual_work_parts(
        inlet_list, data_fn, annual_averaging, y_label, title, limit_fn
    )


def chart_annual_temperature_averages(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing annual temperature plots")
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Temperature (C)",
        "Deep Water Temperature Annual Averages",
        lambda inlet: inlet.limits["temperature"]["deep"]
        if use_limits and "temperature" in inlet.limits
        else [],
    )
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Temperature (C)",
        "Surface Water Temperature Annual Averages",
        lambda inlet: inlet.limits["temperature"]["surface"]
        if use_limits and "temperature" in inlet.limits
        else [],
    )


def chart_annual_temperature_averages_single(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing annual temperature plots")
    y_label = "Temperature (C)"

    data_fn_modified = lambda inlet, category: inlet.get_temperature_data(
        category, do_average=True, before=END
    )
    limit_fn_modified = lambda inlet, depth: inlet.limits["temperature"][
        depth] if use_limits and "temperature" in inlet.limits else []

    category_dict = {'surface': inlets.Category.SURFACE,
                     'deep': inlets.Category.USED_DEEP}

    for inlet_obj in inlet_list:
        title = "{} Surface and Deep Water Temperature Annual Averages".format(
            inlet_obj.name)
        do_annual_work_single(
            inlet_obj, data_fn_modified, annual_averaging, limit_fn_modified,
            title, y_label, category_dict
        )


def chart_annual_salinity_averages(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing annual salinity plots")
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Salinity (PSU)",
        "Deep Water Salinity Annual Averages",
        lambda inlet: inlet.limits["salinity"]["deep"]
        if use_limits and "salinity" in inlet.limits
        else [],
    )
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Salinity (PSU)",
        "Surface Water Salinity Annual Averages",
        lambda inlet: inlet.limits["salinity"]["surface"]
        if use_limits and "salinity" in inlet.limits
        else [],
    )


def chart_annual_oxygen_averages(inlet_list: List[inlets.Inlet], use_limits: bool):
    print("Producing annual oxygen plots")
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.USED_DEEP, do_average=True, before=END
        ),
        "Oxygen (mL/L)",
        "Deep Water Dissolved Oxygen Annual Averages",
        lambda inlet: inlet.limits["oxygen"]["deep"]
        if use_limits and "oxygen" in inlet.limits
        else [],
    )
    do_chart_annual_averages(
        inlet_list,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.USED_SURFACE, do_average=True, before=END
        ),
        "Oxygen (mL/L)",
        "Surface Water Dissolved Oxygen Annual Averages",
        lambda inlet: inlet.limits["oxygen"]["surface"]
        if use_limits and "oxygen" in inlet.limits
        else [],
    )


##############################
# Seasonal Averaging Functions
##############################


def apply_monthly_plot_formatting():
    plt.xlim(0, 13)
    plt.xticks(
        range(1, 13),
        ["JA", "FE", "MR", "AL", "MA", "JN", "JL", "AU", "SE", "OC", "NO", "DE"],
    )


def do_seasonal_averages_work(inlet, data_fn):
    plt.clf()
    times, data = data_fn(inlet)
    plt.plot([time.month for time in times], data, "xg", label=f"Monthly Data")
    apply_monthly_plot_formatting()
    plt.legend()


def do_seasonal_frequency_work(inlet, data_fn):
    plt.clf()
    data = []
    times, _ = data_fn(inlet)
    for time in times:
        data.append(time.month)
    plt.hist(
        data,
        bins=bins(1, 12),
        align="left",
        label=f"Number of data points {len(data)}",
    )
    apply_monthly_plot_formatting()
    plt.legend()


def do_seasonal_trend_comparison(inlet, data_fn, combine_years=False):
    plt.clf()
    times, data = zip(*sorted(zip(*data_fn(inlet)), key=lambda x: x[0]))
    if combine_years:
        times = [time.month for time in times]
    plt.plot(times, data, "xk", label=f"Monthly Data")

    if combine_years:
        indexed = times
        even_spaced = even_times = list(range(1, 13))
    else:
        indexed = utils.index_by_month(times)
        even_spaced = []
        even_times = []
        years = [time.year for time in times]
        for year in range(min(years), max(years) + 1):
            even_spaced.extend(
                [month + 1 + (12 * year - min(years)) for month in range(12)]
            )
            even_times.extend(
                [datetime.date(year, month + 1, 1) for month in range(12)]
            )

    linear_fit = polynomial.Polynomial.fit(indexed, data, 1)
    plt.plot(times, linear_fit(numpy.asarray(indexed)), label=f"Linear Fit")

    mean = utils.mean(data)

    def fit_sin(x, freq, amplitude, phase, offset):
        return numpy.sin(x * freq + phase) * amplitude + offset

    # period given in months
    freq = lambda period: 1 / period
    amp = (max(data) - min(data)) / 2

    popt_sin12, _ = scipy.optimize.curve_fit(
        fit_sin, indexed, data, p0=[freq(12), amp, 1, mean]
    )
    plt.plot(
        even_times,
        [fit_sin(x, *popt_sin12) for x in even_spaced],
        label=f"12 Month Sine Fit",
    )

    popt_sin6, _ = scipy.optimize.curve_fit(
        fit_sin, indexed, data, p0=[freq(6), amp, 1, mean]
    )
    plt.plot(
        even_times,
        [fit_sin(x, *popt_sin6) for x in even_spaced],
        label=f"6 Month Sine Fit",
    )

    popt_sin3, _ = scipy.optimize.curve_fit(
        fit_sin, indexed, data, p0=[freq(3), amp, 1, mean]
    )
    plt.plot(
        even_times,
        [fit_sin(x, *popt_sin3) for x in even_spaced],
        label=f"3 Month Sine Fit",
    )

    if combine_years:
        apply_monthly_plot_formatting()

    plt.legend()


def do_salinity_oxygen_compare(inlet, salinity_fn, oxygen_fn):
    plt.clf()
    sal_times, sal_data = salinity_fn(inlet)
    oxy_times, oxy_data = oxygen_fn(inlet)

    for m, style, name in zip(
        range(1, 13),
        ["xg", "xm", "xb", "xk", "xr", "xc", "+g", "+m", "+b", "+k", "+r", "+c"],
        ["JA", "FE", "MR", "AL", "MA", "JN", "JL", "AU", "SE", "OC", "NO", "DE"],
    ):
        data = list(zip(
            *[
                [s, o]
                for s_t, s in zip(sal_times, sal_data) for o_t, o in zip(oxy_times, oxy_data)
                if s_t == o_t and s_t.month == m
            ]
        ))
        if len(data) < 2:
            continue

        plt.plot(*data, style, label=name)

    plt.legend()


def do_seasonal_salinity_oxygen_compare(inlet, salinity_fn, oxygen_fn):
    plt.clf()
    sal_times, sal_data = salinity_fn(inlet)
    oxy_times, oxy_data = oxygen_fn(inlet)

    for (months, name), style in zip(
        inlet.get_seasons(),
        ["xg", "xm", "xb", "xk", "xr", "xc", "+g", "+m", "+b", "+k", "+r", "+c"],
    ):
        data = list(zip(
            *[
                [s, o]
                for s_t, s in zip(sal_times, sal_data) for o_t, o in zip(oxy_times, oxy_data)
                if s_t == o_t and s_t.month in months
            ]
        ))
        if len(data) < 2:
            continue

        plt.plot(*data, style, label=name)

    plt.legend()


def chart_oxygen_seasonal_trends(inlet: inlets.Inlet):
    print(f"Producing oxygen seasonal trend plots for {inlet.name}")
    bounds = inlet.deep_bounds
    get_data = lambda inlet: inlet.get_oxygen_data(
        inlets.Category.DEEP, do_average=True, before=END
    )
    do_seasonal_averages_work(inlet, get_data)
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Seasonal Trends"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-seasonal-trends.png")
    )

    do_seasonal_frequency_work(inlet, get_data)
    plt.ylabel("Number of Stations")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Seasonal Stations"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-seasonal-stations.png")
    )

    do_seasonal_trend_comparison(inlet, get_data)
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Seasonal Trend Comparison"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-seasonal-comparison.png")
    )

    get_salinity = lambda inlet: inlet.get_salinity_data(inlets.Category.DEEP, do_average=True, before=END)
    do_salinity_oxygen_compare(
        inlet,
        get_salinity,
        get_data,
    )
    plt.xlabel("Salinity (PSU)")
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Salinity Relationship"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-salinity-relationship.png")
    )

    do_seasonal_salinity_oxygen_compare(
        inlet,
        get_salinity,
        get_data,
    )
    plt.xlabel("Salinity (PSU)")
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Salinity Relationship"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-salinity-seasons.png")
    )


#############################
# Decadal averaging functions
#############################


def compute_decadal_average(times, data):
    totals = {}
    for time, datum in zip(times, data):
        year = time.year
        utils.update_totals(totals, year, datum)
    new_data = annual_averaging(totals, [])

    totals = {}
    years = {}
    for year, datum in new_data.items():
        decade = year // 10
        utils.update_totals(totals, decade, datum)
        utils.update_totals(years, decade, year)
    averages = annual_averaging(totals, [])
    years = annual_averaging(years, [])

    return zip(
        *[
            (utils.date_from_float(years[decade]), averages[decade])
            for decade in averages.keys()
        ]
    )


def do_decadal_anomaly_work(inlet, data_fn, use_seasons=False):
    plt.clf()
    times, data = data_fn(inlet)

    # plot bare data along side decadal averages
    if use_seasons:
        means = {}
        seasons = {}
        for season, name in inlet.get_seasons():
            seasons[name] = season
            means[name] = utils.mean([datum for time, datum in zip(times, data) if time.month in season])
        removed_trend = [
            datum - means[name]
            for time, datum in zip(times, data) for name in means.keys()
            if time.month in seasons[name]
        ]
    else:
        removed_trend = utils.remove_seasonal_trend(
            times, data, utils.Trend.NONE, remove_sd=False
        )
    plt.plot(times, removed_trend, "xg", label=f"Monthly Anomalies")

    # plot trend of anomalies across decades
    x, y = compute_decadal_average(times, removed_trend)
    plt.plot(x, y, "^b", label=f"Decadal Anomalies")

    plt.legend()


def do_decadal_averages_work(inlet, data_fn):
    plt.clf()
    times, data = data_fn(inlet)

    # plot bare data along side decadal averages
    plt.plot(times, data, "xg", label=f"Monthly Averages")

    # plot trend of anomalies across decades
    x, y = compute_decadal_average(times, data)
    plt.plot(x, y, "^b", label=f"Decadal Averages")

    plt.legend()


def chart_temperature_decade(inlet: inlets.Inlet):
    print(f"Producing temperature decade trend plots for {inlet.name}")
    bounds = inlet.deep_bounds
    do_decadal_averages_work(
        inlet,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Temperature (C)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Temperature - Decade Averages"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-temperature-decade-averages.png")
    )
    do_decadal_anomaly_work(
        inlet,
        lambda inlet: inlet.get_temperature_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Temperature (C)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Temperature - Decade Anomalies"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-temperature-decade-anomalies.png")
    )


def chart_salinity_decade(inlet: inlets.Inlet):
    print(f"Producing salinity decade trend plot for {inlet.name}")
    bounds = inlet.deep_bounds
    do_decadal_averages_work(
        inlet,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Salinity (PSU)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Salinity - Decade Averages"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-salinity-decade-averages.png")
    )
    do_decadal_anomaly_work(
        inlet,
        lambda inlet: inlet.get_salinity_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Salinity (PSU)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Salinity - Decade Anomalies"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-salinity-decade-anomalies.png")
    )


def chart_oxygen_decade(inlet: inlets.Inlet):
    print(f"Producing oxygen decade trend plot for {inlet.name}")
    bounds = inlet.deep_bounds
    do_decadal_averages_work(
        inlet,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Decade Averages"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-decade-averages.png")
    )
    do_decadal_anomaly_work(
        inlet,
        lambda inlet: inlet.get_oxygen_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
    )
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Decade Anomalies"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-decade-anomalies.png")
    )


def chart_oxygen_decade_seasonal(inlet: inlets.Inlet):
    print(f"Producing oxygen decade trend plot for {inlet.name} accounting for seasonality")
    bounds = inlet.deep_bounds
    do_decadal_anomaly_work(
        inlet,
        lambda inlet:inlet.get_oxygen_data(
            inlets.Category.DEEP, do_average=True, before=END
        ),
        use_seasons=True,
    )
    plt.ylabel("Dissolved Oxygen (mL/L)")
    plt.title(
        f"{inlet.name} {utils.label_from_bounds(*bounds)} Dissolved Oxygen - Decade Seasonal Anomalies"
    )
    plt.savefig(
        figure_path(f"{utils.normalize(inlet.name)}-oxygen-decade-seasonal-anomalies.png")
    )


###################
# Monthly functions
###################


def chart_monthly_sample(inlet: inlets.Inlet):
    months = [
        "padding",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    files = {
        "January": {},
        "February": {},
        "March": {},
        "April": {},
        "May": {},
        "June": {},
        "July": {},
        "August": {},
        "September": {},
        "October": {},
        "November": {},
        "December": {},
    }
    min_year = END.year
    max_year = 0
    for datum in itertools.chain(
        inlet.data.get_temperature_data((None, None)),
        inlet.data.get_salinity_data((None, None)),
        inlet.data.get_oxygen_data((None, None)),
    ):
        year = datum.time.year
        # InletData object doesn't expose date filtering so we do it here
        if year > END.year:
            continue
        min_year = min(year, min_year)
        max_year = max(year, max_year)
        month = months[datum.time.month]
        if year not in files[month]:
            files[month][year] = set()
        files[month][year].add(datum.source)
    year_range = max_year - min_year + 1
    values = []
    for _ in range(year_range):
        values.append([0] * 12)
    for month, d in files.items():
        for year, filenames in d.items():
            year_idx = year - min_year
            month_idx = months.index(month) - 1
            values[year_idx][month_idx] += len(filenames)
    biggest = 0
    for row in values:
        biggest = max(biggest, *row)

    plt.clf()
    matplotlib.rc("axes", titlesize=25)
    matplotlib.rc("xtick", labelsize=20)
    matplotlib.rc("ytick", labelsize=20)
    plt.figure(figsize=(40, 10), constrained_layout=True)
    plt.imshow(list(map(list, zip(*values))), vmin=0, vmax=biggest, cmap="Blues")
    plt.yticks(ticks=range(12), labels=months[1:])
    plt.xticks(
        ticks=range(0, year_range, 2),
        labels=range(min_year, max_year + 1, 2),
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )
    for i, _ in enumerate(values):
        for j, _ in enumerate(values[i]):
            plt.text(
                i,
                j,
                values[i][j],
                ha="center",
                va="center",
                color="k",
                fontsize="large",
            )

    plt.title(f"{inlet.name} Sampling Frequency by Month")
    plt.axis("tight")
    plt.colorbar()
    plt.savefig(figure_path(f"{utils.normalize(inlet.name)}-monthly-sampling.png"))
    plt.close()

    # reset values
    matplotlib.rcdefaults()
    plt.axis("auto")


def main_all():
    parser = argparse.ArgumentParser()
    # inlet retrieval args
    parser.add_argument("-r", "--from-saved", action="store_true")
    parser.add_argument("-n", "--from-netcdf", action="store_true")
    parser.add_argument("-e", "--from-erddap", action="store_true")
    parser.add_argument("-c", "--from-csv", action="store_true")
    parser.add_argument("-d", "--data", type=str, nargs="?", default="data")
    # plot args
    parser.add_argument("-l", "--no-limits", action="store_true")
    parser.add_argument("-i", "--inlet-name", type=str, nargs="+", default=[])
    parser.add_argument("-k", "--limit-name", type=str, nargs="+", default=[])
    parser.add_argument("-I", "--remove-inlet-name", type=str, nargs="+", default=[])
    parser.add_argument("-b", "--plot-buckets", action="store_true")
    parser.add_argument("-a", "--plot-averages", action="store_true")
    parser.add_argument("-A", "--plot-annual", action="store_true")
    parser.add_argument("-R", "--plot-raw", action="store_true")
    parser.add_argument("-s", "--plot-sampling", action="store_true")
    parser.add_argument("-D", "--plot-decadal", action="store_true")
    parser.add_argument(
        "-g", "--geojson", type=str, nargs="?", default="inlets.geojson"
    )
    parser.add_argument("--plot-all", action="store_true")
    args = parser.parse_args()
    inlet_list = inlets.get_inlets(
        args.data,
        from_saved=args.from_saved,
        from_netcdf=args.from_netcdf,
        from_erddap=args.from_erddap,
        from_csv=args.from_csv,
        inlet_names=args.inlet_name,
        drop_names=args.remove_inlet_name,
        keep_names=args.limit_name,
        geojson_file=args.geojson,
    )
    plt.figure(figsize=(8, 6))
    if args.plot_all:
        (
            plot_annual,
            plot_sampling,
            plot_average,
            plot_raw,
            plot_buckets,
            plot_decadal,
        ) = (
            True,
            True,
            True,
            True,
            False,
            False,
        )
    else:
        (
            plot_annual,
            plot_sampling,
            plot_average,
            plot_raw,
            plot_buckets,
            plot_decadal,
        ) = (
            args.plot_annual,
            args.plot_sampling,
            args.plot_averages,
            args.plot_raw,
            args.plot_buckets,
            args.plot_decadal,
        )
    ensure_figure_path()
    if plot_annual:
        chart_annual_temperature_averages(inlet_list, not args.no_limits)
        chart_annual_salinity_averages(inlet_list, not args.no_limits)
        chart_annual_oxygen_averages(inlet_list, not args.no_limits)
        chart_temperature_anomalies(inlet_list, not args.no_limits)
        chart_salinity_anomalies(inlet_list, not args.no_limits)
        chart_oxygen_anomalies(inlet_list, not args.no_limits)
    if plot_sampling:
        for inlet in inlet_list:
            do_chart(
                inlet,
                "samples",
                False,
                chart_stations,
                False,
            )
            chart_monthly_sample(inlet)
    if plot_buckets:
        do_chart_all(
            inlet_list,
            "temperature",
            inlets.Category.DEEP,
            chart_all_temperature,
        )
        do_chart_all(
            inlet_list,
            "temperature",
            inlets.Category.DEEPER,
            chart_all_temperature,
        )
        do_chart_all(
            inlet_list,
            "temperature",
            inlets.Category.DEEPEST,
            chart_all_temperature,
        )
        do_chart_all(inlet_list, "salinity", inlets.Category.DEEP, chart_all_salinity)
        do_chart_all(inlet_list, "salinity", inlets.Category.DEEPER, chart_all_salinity)
        do_chart_all(
            inlet_list, "salinity", inlets.Category.DEEPEST, chart_all_salinity
        )
        do_chart_all(inlet_list, "oxygen", inlets.Category.DEEP, chart_all_oxygen)
        do_chart_all(inlet_list, "oxygen", inlets.Category.DEEPER, chart_all_oxygen)
        do_chart_all(inlet_list, "oxygen", inlets.Category.DEEPEST, chart_all_oxygen)
    if plot_average:
        for inlet in inlet_list:
            do_chart(
                inlet,
                "temperature",
                not args.no_limits,
                chart_temperatures,
                True,
            )
            do_chart(
                inlet,
                "salinity",
                not args.no_limits,
                chart_salinities,
                True,
            )
            do_chart(
                inlet,
                "oxygen",
                not args.no_limits,
                chart_oxygen_data,
                True,
            )
    if plot_raw:
        for inlet in inlet_list:
            do_chart(
                inlet,
                "temperature",
                not args.no_limits,
                chart_temperatures,
                False,
            )
            do_chart(
                inlet,
                "salinity",
                not args.no_limits,
                chart_salinities,
                False,
            )
            do_chart(
                inlet,
                "oxygen",
                not args.no_limits,
                chart_oxygen_data,
                False,
            )
    if plot_decadal:
        for inlet in inlet_list:
            chart_temperature_decade(inlet)
            chart_salinity_decade(inlet)
            chart_oxygen_decade(inlet)
            chart_oxygen_seasonal_trends(inlet)
            chart_oxygen_decade_seasonal(inlet)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    # inlet retrieval args
    parser.add_argument("-r", "--from-saved", action="store_true")
    parser.add_argument("-n", "--from-netcdf", action="store_true")
    parser.add_argument("-e", "--from-erddap", action="store_true")
    parser.add_argument("-c", "--from-csv", action="store_true")
    parser.add_argument("-d", "--data", type=str, nargs="?", default="data")
    # plot args
    parser.add_argument("-l", "--no-limits", action="store_true")
    parser.add_argument("-i", "--inlet-name", type=str, nargs="+", default=[])
    parser.add_argument("-k", "--limit-name", type=str, nargs="+", default=[])
    parser.add_argument("-I", "--remove-inlet-name", type=str, nargs="+", default=[])
    parser.add_argument("-b", "--plot-buckets", action="store_true")
    parser.add_argument("-a", "--plot-averages", action="store_true")
    parser.add_argument("-A", "--plot-annual", action="store_true")
    parser.add_argument("-R", "--plot-raw", action="store_true")
    parser.add_argument("-s", "--plot-sampling", action="store_true")
    parser.add_argument("-D", "--plot-decadal", action="store_true")
    parser.add_argument(
        "-g", "--geojson", type=str, nargs="?", default="burke_inlet.geojson"
    )
    parser.add_argument("--plot-all", action="store_true")
    args = parser.parse_args()
    osd_data_dir = '/usb/OSD_Data_Archive/'  # Access cruise and netCDF data
    hakai_data_dir = '/home/hourstonh/Documents/inlets/hakai_data/'
    inlet_list = inlets.get_burke_inlet(
        osd_data_dir, hakai_data_dir,
        from_saved=args.from_saved,
        from_netcdf=args.from_netcdf,
        from_erddap=args.from_erddap,
        from_csv=args.from_csv,
        inlet_names=args.inlet_name,
        drop_names=args.remove_inlet_name,
        keep_names=args.limit_name,
        geojson_file=args.geojson,
    )
    # inlet_list = inlets.get_burke_inlet(
    #     osd_data_dir, hakai_data_dir,
    #     from_saved=False,
    #     from_netcdf=True,
    #     from_erddap=False,
    #     from_csv=True,
    #     inlet_names=args.inlet_name,
    #     drop_names=args.remove_inlet_name,
    #     keep_names=args.limit_name,
    #     geojson_file=args.geojson,
    # )
    # print('inlet_list:', inlet_list)
    plt.figure(figsize=(8, 6))
    if args.plot_all:
        (
            plot_annual,
            plot_sampling,
            plot_average,
            plot_raw,
            plot_buckets,
            plot_decadal,
        ) = (
            True,
            True,
            True,
            True,
            False,
            False,
        )
    else:
        (
            plot_annual,
            plot_sampling,
            plot_average,
            plot_raw,
            plot_buckets,
            plot_decadal,
        ) = (
            args.plot_annual,
            args.plot_sampling,
            args.plot_averages,
            args.plot_raw,
            args.plot_buckets,
            args.plot_decadal,
        )
    ensure_figure_path()
    if plot_annual:
        chart_annual_temperature_averages_single(inlet_list, not args.no_limits)
        chart_temperature_anomalies_single(inlet_list, not args.no_limits)
    #     chart_annual_temperature_averages_select(inlet_list, use_limits:Bool)
    #     chart_annual_temperature_averages_select(inlet_list, not args.no_limits)
    if plot_average:
        for inlet in inlet_list:
            # do_chart(inlet, kind, use_limits, chart_fn, use_averages:Bool)
            do_chart(
                inlet,
                "temperature",
                False,  # not args.no_limits,
                chart_temperatures_surface_deep,
                True,
            )
    plt.close()


if __name__ == "__main__":
    main()
