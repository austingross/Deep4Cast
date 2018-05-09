# -*- coding: utf-8 -*-
"""This script provides command line access for testing forecasters on
custom data sets.

Example:
    $python deep4cast.py --data-path "./tutorials/timeseries_data.csv" --lookback_period 20 --test-fraction 0.1

"""
import argparse
from pprint import pprint

from deep4cast.forecasters import CNNForecaster, RNNForecaster
from pandas import read_table
from deep4cast.utils import compute_mape


def main(args):
    """Main function that handles forecasting given list of arugments."""
    # Load training at test data from file input
    print("\n\nLoading datasets.")
    df = read_table(args.data_path, sep=',')
    ts = df.values

    # Prepare train and test set. Make sure to catch the case when the user
    # did not supply a test. We use the end of the time series for testing
    # because of lookahead bias.
    if args.test_fraction:
        test_length = int(len(df) * args.test_fraction)
        train_length = len(df) - test_length
        ts_train = ts[:-test_length]
        ts_test = ts[-test_length - args.lookback_period:]
    else:
        ts_train = ts


    # Why isn't topology an option?
    print('\n\nBuild a CNN wihtout uncertainty:')
    topology = [({'layer': 'Conv1D', 'id': 'c1', 'parent': 'input'},
                 {'filters': 64, 'kernel_size': 5, 'activation': 'elu'}),
                ({'layer': 'MaxPooling1D', 'id': 'mp1', 'parent': 'c1'},
                 {'pool_size': 3, 'strides': 1}),
                ({'layer': 'Conv1D', 'id': 'c2', 'parent': 'mp1'},
                 {'filters': 64, 'kernel_size': 3, 'activation': 'elu'}),
                ({'layer': 'MaxPooling1D', 'id': 'mp2', 'parent': 'c2'},
                 {'pool_size': 4, 'strides': 2}),
                ({'layer': 'Conv1D', 'id': 'c3', 'parent': 'mp2'},
                 {'filters': 128, 'kernel_size': 3, 'activation': 'elu'}),
                ({'layer': 'MaxPooling1D', 'id': 'mp3', 'parent': 'c3'},
                 {'pool_size': 3, 'strides': 1}),
                ({'layer': 'Flatten', 'id': 'f1', 'parent': 'mp3'},
                 {}),
                ({'layer': 'Dense', 'id': 'd1', 'parent': 'f1'},
                 {'units': 128, 'activation': 'elu'}),
                ({'layer': 'Dense', 'id': 'output', 'parent': 'd1'},
                 {'units': 128, 'activation': 'elu'})]
    forecaster = CNNForecaster(
        topology,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        uncertainty='last'
    )
    forecaster.fit(ts_train, lookback_period=args.lookback_period)

    # Print errors to screen using a specified metric function
    metric = compute_mape
    if args.test_fraction:
        print(
            'TRAIN \t Mean Absolute Percentage Error: {0:.1f}%'.format(
                metric(
                    forecaster, ts_train, ts[args.lookback_period:train_length]
                )
            )
        )
        print(
            'TEST \t Mean Absolute Percentage Error: {0:.1f}%'.format(
                metric(forecaster, ts_test, ts[train_length:])
            )
        )
    else:
        print(
            'TRAIN \t Mean Absolute Percentage Error: {0:.1f}%'.format(
                metric(forecaster, ts_train, ts[args.lookback_period:])
            )
        )


# Putting the parser out makes it easier to change the parameters from within a Python script/function.
# https://gist.github.com/zer0n/d11cc130c5a35fabd6e1be961ead8576 is an example.
def _get_parser():
    # Collect all relevant command line arguments
    parser = argparse.ArgumentParser()
    named_args = parser.add_argument_group('named arguments')

    named_args.add_argument('-d', '--data-path',
                            help="Location of data set",
                            required=True,
                            type=str)

    named_args.add_argument('-tf', '--test-fraction',
                            help="Test fraction at end of dataset",
                            required=False,
                            default=None,
                            type=float)

    named_args.add_argument('-lb', '--lookback_period',
                            help="Lookback period",
                            required=True,
                            type=int)

    named_args.add_argument('-e', '--epochs',
                            help="Number of epochs to run",
                            required=False,
                            default=100,
                            type=int)

    named_args.add_argument('-b', '--batch-size',
                            help="Location of validation data",
                            required=False,
                            default=8,
                            type=int)

    named_args.add_argument('-lr', '--learning-rate',
                            help="Learning rate",
                            required=False,
                            default=0.1,
                            type=float)


if __name__ == '__main__':
    args = _get_parser().parse_args()
    main(args)