import numpy as np
from ..core_chart import BaseChart


class BaseAggregateChart(BaseChart):

    use_data_tiles = True
    custom_binning = False

    def _compute_array_all_bins(
        self, source_x, source_y, update_data_x, update_data_y
    ):
        """
        source_x: current_source_x, np.array()
        source_y: current_source_y, np.array()
        update_data_x: updated_data_x, np.array()
        update_data_y: updated_data_x, np.array()
        """
        result_array = np.zeros(shape=(int(source_x.max()),))
        # -1 for 0-based indexing
        np.put(result_array, update_data_x.astype(int) - 1, update_data_y)
        return result_array[source_x.astype(int) - 1]

    def query_chart_by_range(self, active_chart, query_tuple, datatile):
        """
        Description:

        -------------------------------------------
        Input:
            1. active_chart: chart object of active_chart
            2. query_tuple: (min_val, max_val) of the query [type: tuple]
            3. datatile: datatile of active chart for
                            current chart[type: pandas df]
        -------------------------------------------

        Ouput:
        """
        min_val, max_val = query_tuple
        datatile_index_min = int(
            round((min_val - active_chart.min_value) / active_chart.stride)
        )
        datatile_index_max = int(
            round((max_val - active_chart.min_value) / active_chart.stride)
        )
        if self.custom_binning:
            datatile_indices = self.source.data[self.data_x_axis]
        else:
            datatile_indices = (
                (self.source.data[self.data_x_axis] - self.min_value)
                / self.stride
            ).astype(int)

        if datatile_index_min == 0:
            if self.aggregate_fn == "mean":
                datatile_result_sum = np.array(
                    datatile[0].loc[datatile_indices, datatile_index_max]
                )
                datatile_result_count = np.array(
                    datatile[1].loc[datatile_indices, datatile_index_max]
                )
                datatile_result = datatile_result_sum / datatile_result_count
            elif self.aggregate_fn in ["count", "sum", "min", "max"]:
                datatile_result = datatile.loc[
                    datatile_indices, datatile_index_max
                ]
        else:
            datatile_index_min -= 1
            if self.aggregate_fn == "mean":
                datatile_max0 = datatile[0].loc[
                    datatile_indices, datatile_index_max
                ]
                datatile_min0 = datatile[0].loc[
                    datatile_indices, datatile_index_min
                ]
                datatile_result_sum = np.array(datatile_max0 - datatile_min0)

                datatile_max1 = datatile[1].loc[
                    datatile_indices, datatile_index_max
                ]
                datatile_min1 = datatile[1].loc[
                    datatile_indices, datatile_index_min
                ]
                datatile_result_count = np.array(datatile_max1 - datatile_min1)

                datatile_result = datatile_result_sum / datatile_result_count
            elif self.aggregate_fn in ["count", "sum"]:
                datatile_max = datatile.loc[
                    datatile_indices, datatile_index_max
                ]
                datatile_min = datatile.loc[
                    datatile_indices, datatile_index_min
                ]
                datatile_result = np.array(datatile_max - datatile_min)
            elif self.aggregate_fn in ["min", "max"]:
                datatile_result = np.array(
                    getattr(
                        datatile.loc[
                            datatile_indices,
                            datatile_index_min:datatile_index_max,
                        ],
                        self.aggregate_fn,
                    )(axis=1, skipna=True)
                )

        self.reset_chart(datatile_result)

    def query_chart_by_indices_for_mean(
        self,
        active_chart,
        old_indices,
        new_indices,
        datatile,
        calc_new,
        remove_old,
    ):
        """
        Description:

        -------------------------------------------
        Input:
        -------------------------------------------

        Ouput:
        """
        if self.custom_binning:
            datatile_indices = self.source.data[self.data_x_axis]
        else:
            datatile_indices = (
                (self.source.data[self.data_x_axis] - self.min_value)
                / self.stride
            ).astype(int)
        if len(new_indices) == 0 or new_indices == [""]:
            datatile_sum_0 = np.array(
                datatile[0].loc[datatile_indices].sum(axis=1, skipna=True)
            )
            datatile_sum_1 = np.array(
                datatile[1].loc[datatile_indices].sum(axis=1, skipna=True)
            )
            datatile_result = datatile_sum_0 / datatile_sum_1
            return datatile_result

        len_y_axis = datatile[0][0].loc[datatile_indices].shape[0]

        datatile_result = np.zeros(shape=(len_y_axis,), dtype=np.float64)
        value_sum = np.zeros(shape=(len_y_axis,), dtype=np.float64)
        value_count = np.zeros(shape=(len_y_axis,), dtype=np.float64)

        for index in new_indices:
            index = int(
                round((index - active_chart.min_value) / active_chart.stride)
            )
            value_sum += datatile[0][int(index)].loc[datatile_indices]
            value_count += datatile[1][int(index)].loc[datatile_indices]

        datatile_result = value_sum / value_count

        return datatile_result

    def query_chart_by_indices_for_count(
        self,
        active_chart,
        old_indices,
        new_indices,
        datatile,
        calc_new,
        remove_old,
    ):
        """
        Description:

        -------------------------------------------
        Input:
        -------------------------------------------

        Ouput:
        """
        if self.custom_binning:
            datatile_indices = self.source.data[self.data_x_axis]
        else:
            datatile_indices = (
                (self.source.data[self.data_x_axis] - self.min_value)
                / self.stride
            ).astype(int)
        if len(new_indices) == 0 or new_indices == [""]:
            datatile_result = np.array(
                datatile.loc[datatile_indices, :].sum(axis=1, skipna=True)
            )
            return datatile_result

        if len(old_indices) == 0 or old_indices == [""]:
            len_y_axis = datatile.loc[datatile_indices, 0].shape[0]
            datatile_result = np.zeros(shape=(len_y_axis,), dtype=np.float64)
        else:
            len_y_axis = datatile.loc[datatile_indices, 0].shape[0]
            datatile_result = np.array(
                self.get_source_y_axis(), dtype=np.float64
            )[:len_y_axis]

        for index in calc_new:
            index = int(
                round((index - active_chart.min_value) / active_chart.stride)
            )
            datatile_result += np.array(
                datatile.loc[datatile_indices, int(index)]
            )

        for index in remove_old:
            index = int(
                round((index - active_chart.min_value) / active_chart.stride)
            )
            datatile_result -= np.array(
                datatile.loc[datatile_indices, int(index)]
            )

        return datatile_result

    def query_chart_by_indices_for_minmax(
        self, active_chart, old_indices, new_indices, datatile,
    ):
        """
        Description:

        -------------------------------------------
        Input:
        -------------------------------------------

        Ouput:
        """
        if self.custom_binning:
            datatile_indices = self.source.data[self.data_x_axis]
        else:
            datatile_indices = (
                (self.source.data[self.data_x_axis] - self.min_value)
                / self.stride
            ).astype(int)

        if len(new_indices) == 0 or new_indices == [""]:
            # get min or max from datatile df, skipping column 0(always 0)
            datatile_result = np.array(
                getattr(datatile.loc[datatile_indices, 1:], self.aggregate_fn)(
                    axis=1, skipna=True
                )
            )
        else:
            new_indices = np.array(new_indices)
            new_indices = np.round(
                (new_indices - active_chart.min_value) / active_chart.stride
            ).astype(int)
            datatile_result = np.array(
                getattr(
                    datatile.loc[datatile_indices, list(new_indices)],
                    self.aggregate_fn,
                )(axis=1, skipna=True)
            )

        return datatile_result

    def query_chart_by_indices(
        self, active_chart, old_indices, new_indices, datatile
    ):
        """
        Description:

        -------------------------------------------
        Input:
            1. active_chart: chart object of active_chart
            2. query_tuple: (min_val, max_val) of the query [type: tuple]
            3. datatile: datatile of active chart for
                        current chart[type: pandas df]
        -------------------------------------------

        Ouput:
        """
        calc_new = list(set(new_indices) - set(old_indices))
        remove_old = list(set(old_indices) - set(new_indices))

        if "" in calc_new:
            calc_new.remove("")
        if "" in remove_old:
            remove_old.remove("")

        if self.aggregate_fn == "mean":
            datatile_result = self.query_chart_by_indices_for_mean(
                active_chart,
                old_indices,
                new_indices,
                datatile,
                calc_new,
                remove_old,
            )
        elif self.aggregate_fn in ["count", "sum"]:
            datatile_result = self.query_chart_by_indices_for_count(
                active_chart,
                old_indices,
                new_indices,
                datatile,
                calc_new,
                remove_old,
            )
        elif self.aggregate_fn in ["min", "max"]:
            datatile_result = self.query_chart_by_indices_for_minmax(
                active_chart, old_indices, new_indices, datatile,
            )
        self.reset_chart(datatile_result)
