# import pandas as pd
# import numpy as np
# import ruptures as rpt
# import matplotlib.pyplot as plt
# from typing import List, Tuple, Dict
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from dataclasses import dataclass
# import cupy as cp
# from numba import jit
# import warnings
# from collections import OrderedDict
# import logging
# from functools import partial
#
# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# @dataclass
# class ChannelResult:
#     """Dataclass for storing channel analysis results"""
#     changepoints: np.ndarray
#     signal: np.ndarray
#     segments: List[Tuple[int, int]]
#     stats: Dict[str, np.ndarray]
#
#
# class Segmenter:
#     def __init__(self, use_gpu: bool = True, n_threads: int = None) -> None:
#         """
#         Initialize the segmenter with optional GPU support and thread count.
#
#         Args:
#             use_gpu: Whether to use GPU acceleration if available
#             n_threads: Number of threads to use for parallel processing
#         """
#         self.use_gpu = use_gpu and self._check_gpu_availability()
#         self.n_threads = n_threads or ThreadPoolExecutor()._max_workers
#         self.xp = cp if self.use_gpu else np
#         logger.info(f"Initialized segmenter with GPU={self.use_gpu}, threads={self.n_threads}")
#
#     @staticmethod
#     def _check_gpu_availability() -> bool:
#         """Check if GPU is available for computation"""
#         try:
#             import cupy as cp
#             cp.cuda.runtime.getDeviceCount()
#             return True
#         except:
#             warnings.warn("GPU not available, falling back to CPU")
#             return False
#
#     @staticmethod
#     @jit(nopython=True)
#     def _normalize_signal(signal: np.ndarray) -> np.ndarray:
#         """Normalize signal using Numba-accelerated computation"""
#         mean = np.mean(signal)
#         std = np.std(signal)
#         return (signal - mean) / (std if std != 0 else 1)
#
#     def _process_signal_gpu(self, signal: np.ndarray) -> np.ndarray:
#         """Process signal on GPU if available"""
#         if self.use_gpu:
#             signal_gpu = cp.asarray(signal)
#             normalized = (signal_gpu - cp.mean(signal_gpu)) / cp.std(signal_gpu)
#             return cp.asnumpy(normalized)
#         return self._normalize_signal(signal)
#
#     def detect_changepoints(self, signal: np.ndarray, penalty_value: float = 1) -> ChannelResult:
#         """
#         Detect changepoints in a single channel with optimized processing.
#
#         Args:
#             signal: Input signal array
#             penalty_value: Penalty value for changepoint detection
#
#         Returns:
#             ChannelResult object containing changepoints and statistics
#         """
#         # Normalize signal using GPU or CPU optimization
#         normalized_signal = self._process_signal_gpu(signal)
#
#         # Use ruptures with optimal parameters
#         algo = rpt.Binseg(model="l2", jump=5).fit(normalized_signal.reshape(-1, 1))
#         changepoints = np.array(algo.predict(pen=penalty_value)[:-1])
#
#         # Calculate segments
#         segments = list(zip([0] + list(changepoints),
#                             list(changepoints) + [len(signal)]))
#
#         # Calculate segment statistics
#         stats = self._calculate_segment_stats(normalized_signal, segments)
#
#         return ChannelResult(
#             changepoints=changepoints,
#             signal=normalized_signal,
#             segments=segments,
#             stats=stats
#         )
#
#     def _calculate_segment_stats(self, signal: np.ndarray,
#                                  segments: List[Tuple[int, int]]) -> Dict[str, np.ndarray]:
#         """Calculate statistics for each segment"""
#         stats = {
#             'means': np.array([np.mean(signal[start:end]) for start, end in segments]),
#             'stds': np.array([np.std(signal[start:end]) for start, end in segments]),
#             'lengths': np.array([end - start for start, end in segments])
#         }
#         return stats
#
#     def _process_channel(self, channel_data: Tuple[str, np.ndarray],
#                          penalty_value: float) -> Tuple[str, ChannelResult]:
#         """Process a single channel for parallel execution"""
#         channel_name, signal = channel_data
#         try:
#             result = self.detect_changepoints(signal, penalty_value)
#             return channel_name, result
#         except Exception as e:
#             logger.error(f"Error processing channel {channel_name}: {str(e)}")
#             raise
#
#     def analyze_all_channels(self, df: pd.DataFrame, penalty_value: float = 1) -> OrderedDict:
#         """
#         Analyze all channels in parallel with optimized processing.
#
#         Args:
#             df: Input DataFrame with time series data
#             penalty_value: Penalty value for changepoint detection
#
#         Returns:
#             OrderedDict containing results for each channel
#         """
#         results = OrderedDict()
#         channel_data = [(col, df[col].values) for col in df.columns[1:]]
#
#         process_func = partial(self._process_channel, penalty_value=penalty_value)
#
#         with ThreadPoolExecutor(max_workers=self.n_threads) as executor:
#             future_to_channel = {
#                 executor.submit(process_func, data): data[0]
#                 for data in channel_data
#             }
#
#             for future in as_completed(future_to_channel):
#                 channel_name, result = future.result()
#                 results[channel_name] = result
#
#         return results
#
#     def plot_results(self, df: pd.DataFrame, results: OrderedDict,
#                      figsize: Tuple[int, int] = (15, 20)) -> plt.Figure:
#         """
#         Plot results with enhanced visualization.
#
#         Args:
#             df: Input DataFrame
#             results: Analysis results
#             figsize: Figure size
#
#         Returns:
#             matplotlib Figure object
#         """
#         n_channels = len(results)
#         fig, axes = plt.subplots(n_channels, 1, figsize=figsize)
#         if n_channels == 1:
#             axes = [axes]
#
#         for idx, (channel, result) in enumerate(results.items()):
#             ax = axes[idx]
#
#             # Plot signal
#             ax.plot(df['Time'], result.signal, 'b-', label='Signal', linewidth=1)
#
#             # Plot segments with different colors
#             for i, (start, end) in enumerate(result.segments):
#                 mean_level = result.stats['means'][i]
#                 ax.axhline(y=mean_level,
#                            xmin=df['Time'].iloc[start] / df['Time'].iloc[-1],
#                            xmax=df['Time'].iloc[end - 1] / df['Time'].iloc[-1],
#                            color='g', linestyle='--', alpha=0.5)
#
#             # Plot changepoints
#             for cp in result.changepoints:
#                 ax.axvline(x=df['Time'].iloc[cp], color='r',
#                            linestyle='--', alpha=0.5)
#
#             ax.set_title(f'{channel} Changepoints')
#             ax.set_xlabel('Time')
#             ax.set_ylabel('Normalized Amplitude')
#             ax.grid(True, alpha=0.3)
#
#             # Add segment statistics
#             stats_text = f'Segments: {len(result.segments)}\n'
#             ax.text(0.02, 0.98, stats_text,
#                     transform=ax.transAxes,
#                     verticalalignment='top',
#                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
#
#         plt.tight_layout()
#         return fig
#
#
# # Example usage
# if __name__ == "__main__":
#     # Initialize segmenter with GPU support if available
#     segmenter = Segmenter(use_gpu=True)
#
#     # Example data processing
#     try:
#         # Your data loading here
#         df = pd.DataFrame()  # Replace with your data
#         results = segmenter.analyze_all_channels(df)
#         fig = segmenter.plot_results(df, results)
#         plt.show()
#     except Exception as e:
#         logger.error(f"Error in main execution: {str(e)}")

# from joblib import Parallel, delayed
# import ruptures as rpt
# import numpy as np
#
# def run_change_detection(segment):
#     model = "l2"
#     algo = rpt.Binseg(model=model).fit(segment)
#     result = algo.predict(pen=10)
#     return result
#
#
# class Segmenter:
#
#     def __init__(self) -> None:
#         pass
#
#     def segment_signal(self, signal: np.ndarray) -> np.ndarray:
#         num_chunks = 4
#         chunk_size = signal.shape[0] // num_chunks
#         data_chunks = [signal[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]
#         results = Parallel(n_jobs=-1)(delayed(run_change_detection)(chunk) for chunk in data_chunks)
#
#         # Combine results from all chunks and convert them into a single array
#         results = np.concatenate(results)
#
#         return results


import numpy as np
import matplotlib.pyplot as plt
import ruptures as rpt


class Segmenter:
    def __init__(self):
        """
        Initialize the SignalSegmentation object.

        Parameters:
        signal : np.ndarray
            Multi-channel signal to be segmented (shape: [samples, channels]).
        model : str
            Model type for ruptures (e.g., "l1", "l2", "rbf").
        """
        pass

    def fit(self, signal, model, pen=500, n_bkps=None):
        """
        Fit the segmentation model to the signal.

        Parameters:
        pen : float
            Penalty value used in the prediction (used when n_bkps is None).
        n_bkps : int or None
            Number of breakpoints (if known, overrides pen).

        Returns:
        list of breakpoints.
        """
        # Initialize the model
        # algo = rpt.Binseg(model=model).fit(signal)
        # algo = rpt.Pelt(model=model).fit(signal)
        # algo = rpt.Window(width=2, model=model).fit(signal)
        # algo = rpt.Dynp(model=model).fit(signal)
        algo = rpt.BottomUp(model=model).fit(signal)

        # Predict the breakpoints
        if n_bkps:
            self.bkps = algo.predict(n_bkps=n_bkps)
        else:
            self.bkps = algo.predict(pen=pen)

        return self.bkps

    def plot_results(self):
        """
        Plot the signal with the detected breakpoints.
        """
        n_channels = self.signal.shape[1]
        fig, axes = plt.subplots(n_channels, 1, figsize=(10, 8))

        if n_channels == 1:
            axes = [axes]  # Ensure axes is iterable for a single channel

        for i, ax in enumerate(axes):
            ax.plot(self.signal[:, i], label=f'Channel {i + 1}')
            for bkpt in self.bkps:
                ax.axvline(x=bkpt, color='red', linestyle='--')
            ax.legend(loc='best')

        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Generate synthetic signal for testing (multi-channel)
    n = 150000  # 150k samples
    n_channels = 7
    n_bkps, sigma = 7, 5
    signal, bkps = rpt.pw_constant(n, n_bkps, noise_std=sigma, n_features=n_channels)

    # Instantiate the segmentation class and fit the model
    segmenter = Segmenter(signal)
    detected_bkps = segmenter.fit(pen=500)

    # Plot the results
    segmenter.plot_results()
