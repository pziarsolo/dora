from collections import OrderedDict

import numpy as np


def calc_coverage_stats(depths, is_counter=True,
                        percentiles=(0, 20, 40, 60, 80, 100),
                        covs_to_study=(1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100)):
    if is_counter:
        stats = calc_coverage_stats_counter(depths, percentiles, covs_to_study)
    else:
        stats = calc_coverage_stats_np(depths, percentiles, covs_to_study)
    return stats


def calc_coverage_stats_counter(depths, percentiles, covs_to_study):
    stats = OrderedDict()
    stats['min'] = min(depths.keys())
    stats['max'] = max(depths.keys())
    len_values = sum(depths.values())
    stats['length_analysed_regions'] = len_values
    stats['bases_covered'] = sum(count for dp, count in depths.items() if dp != 0)
    stats['bases_uncovered'] = depths[0] if 0 in depths else 0
    mean = sum(dp * count for dp, count in depths.items()) / len_values
    stats['mean'] = mean

    numerator = 0
    for dp, count in depths.items():
        numerator += sum([(dp - mean) ** 2] * count)
    std = pow(numerator / (sum(depths.values()) - 1), 0.5)
    stats['std'] = std

    # median
    value_in_the_middle = sum(depths.values()) / 2
    count_min, count_max = 0, 0
    median = None
    for dp, count in depths.items():
        count_max += count
        if count_min <= value_in_the_middle <= count_max:
            median = dp
            break
        count_min += count
    if median is None:
        raise
    stats['median'] = median

    positions_with_min_cov_values = {}
    for min_cov in covs_to_study:
        positions_with_min_cov_values[min_cov] = sum(count for dp, count in depths.items() if dp >= min_cov)
    stats['range_covs'] = positions_with_min_cov_values
    stats['uniformity_coverage_pct0.2'] = sum(count for dp, count in depths.items() if dp >= mean * 0.2) / len_values
    stats['uniformity_coverage_pct0.5'] = sum(count for dp, count in depths.items() if dp >= mean * 0.5) / len_values

    return stats


def calc_coverage_stats_np(depths, percentiles, covs_to_study):
    stats = OrderedDict()
    stats['min'] = np.min(depths)
    stats['max'] = np.max(depths)
    stats['median'] = np.median(depths)
    stats['mean'] = np.mean(depths)
    stats['std'] = np.std(depths)
    # stats['variance'] = np.var(depths)
    stats['bases_covered'] = np.count_nonzero(depths)
    stats['bases_uncovered'] = np.count_nonzero(depths == 0)
    stats['length_analysed_regions'] = len(depths)
    # depths_percentile20 = depths[depths <= np.percentile(depths, 20)]
    bases_above_02average = np.count_nonzero(depths > np.average(depths) * 0.2)
    stats['uniformity_coverage_pct0.2'] = bases_above_02average / len(depths)
    # stats['percentiles'] = {a: b for a, b in zip(percentiles, np.percentile(depths, percentiles))}
    stats['range_covs'] = {}
    positions_with_min_cov_values = {}
    for min_cov in covs_to_study:
        positions_with_min_cov_values[min_cov] = np.count_nonzero(depths <= min_cov)
    stats['range_covs'] = positions_with_min_cov_values
    return stats


def write_coverage_stats(stats, sample, out_fhand, genome_size=None):
    stdout = f'Data for sample {sample}\n'
    stdout += '-------------------------------\n'
    stdout += f'Minimum coverage value: {stats["min"]}\n'
    stdout += f'Maximum coverage value: {stats["max"]}\n'
    stdout += f'Mean: {stats["mean"]:.2f}\n'
    stdout += f'Std. Desv: {stats["std"]:.2f}\n'
    # stdout += f'Variance: {stats["variance"]:.2f}\n'
    stdout += f'Median: {stats["median"]:.2f}\n'
    stdout += f'Bases covered: {stats["bases_covered"]}\n'
    stdout += f'Bases uncovered: {stats["bases_uncovered"]}\n'
    stdout += f'Length of analysed region: {stats["length_analysed_regions"]}\n'
    stdout += f'Uniformity of Coverage (Pct > 0.2*mean): {stats["uniformity_coverage_pct0.2"]:.2f}\n'
    stdout += f'Uniformity of Coverage (Pct > 0.5*mean): {stats["uniformity_coverage_pct0.5"]:.2f}\n'
    # stdout += f'Percentiles: {", ".join(f"{perct}: {val}" for perct, val in stats["percentiles"].items())}\n'
    stdout += '\n'
    stdout += 'Positions with the given coverage:\n'
    stdout += '----------------------------------\n'
    stdout += 'Depth\tcount\t% total bases\n'

    for min_cov, count_bases, in stats['range_covs'].items():
        percent_total_bases = count_bases / stats["length_analysed_regions"]
        stdout += f'{min_cov}\t{count_bases}\t{percent_total_bases:.2%}\n'

    out_fhand.write(stdout)
