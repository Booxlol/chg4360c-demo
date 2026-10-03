import os

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        """
        Utility class used to monitor bioprocesses by
        generating dashboards and summaries.
        """

        self.df = pd.read_csv(filepath)
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims

    def extract_batch(self, batch_id):
        """
        Extract data corresponding to one batch.
        """

        df_batch = self.df[self.df["batch_id"] == batch_id].copy()

        # Keep measurements in chronological order
        df_batch = df_batch.sort_values("time_h")

        return df_batch

    def optimal_ph_mask(self, df_batch):
        """
        Return True for measurements inside the acceptable pH range.
        """

        return df_batch["pH"].between(
            self.ph_lims[0],
            self.ph_lims[1],
            inclusive="both"
        )

    def optimal_temperature_mask(self, df_batch):
        """
        Return True for measurements inside the acceptable temperature range.
        """

        return df_batch["temperature_C"].between(
            self.temperature_lims[0],
            self.temperature_lims[1],
            inclusive="both"
        )

    def get_n_batches(self):
        """
        Return the number of unique batches.
        """

        return self.df["batch_id"].nunique()

    def export_dashboard(self, batch_id, filepath):
        """
        Create and save a 2 x 2 dashboard for one batch.
        """

        df_batch = self.extract_batch(batch_id)

        ph_mask = self.optimal_ph_mask(df_batch)
        temperature_mask = self.optimal_temperature_mask(df_batch)

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # -------------------------------------------------
        # Top-left: concentrations
        # -------------------------------------------------
        ax = axes[0, 0]

        ax.scatter(
            df_batch["time_h"],
            df_batch["C_glucose_g_L^-1"],
            marker="o",
            label="Glucose"
        )

        ax.scatter(
            df_batch["time_h"],
            df_batch["C_biomass_g_L^-1"],
            marker="s",
            label="Biomass"
        )

        ax.scatter(
            df_batch["time_h"],
            df_batch["C_product_g_L^-1"],
            marker="^",
            label="Product"
        )

        ax.set_title("Concentrations")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Concentration (g/L)")
        ax.legend()

        # -------------------------------------------------
        # Top-right: temperature
        # -------------------------------------------------
        ax = axes[0, 1]

        ax.scatter(
            df_batch.loc[temperature_mask, "time_h"],
            df_batch.loc[temperature_mask, "temperature_C"],
            color="green",
            marker="o",
            label="Within range"
        )

        ax.scatter(
            df_batch.loc[~temperature_mask, "time_h"],
            df_batch.loc[~temperature_mask, "temperature_C"],
            color="red",
            marker="x",
            label="Outside range"
        )

        ax.set_title("Temperature")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Temperature (°C)")
        ax.legend()

        # -------------------------------------------------
        # Bottom-left: pH
        # -------------------------------------------------
        ax = axes[1, 0]

        ax.scatter(
            df_batch.loc[ph_mask, "time_h"],
            df_batch.loc[ph_mask, "pH"],
            color="green",
            marker="o",
            label="Within range"
        )

        ax.scatter(
            df_batch.loc[~ph_mask, "time_h"],
            df_batch.loc[~ph_mask, "pH"],
            color="red",
            marker="x",
            label="Outside range"
        )

        ax.set_title("pH")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("pH")
        ax.legend()

        # -------------------------------------------------
        # Bottom-right: dissolved oxygen
        # -------------------------------------------------
        ax = axes[1, 1]

        ax.scatter(
            df_batch["time_h"],
            df_batch["DO_percent"]
        )

        ax.set_title("Dissolved Oxygen")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Dissolved Oxygen (%)")

        # Use 6-hour tick spacing on every x-axis
        for ax in axes.flat:
            ax.xaxis.set_major_locator(MultipleLocator(6))

        fig.suptitle(f"Batch {batch_id}")
        fig.tight_layout()

        output_directory = os.path.dirname(filepath)

        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        fig.savefig(filepath)
        plt.close(fig)

    def export_summary(self, filepath):
        """
        Generate and save the batch summary table.
        """

        summary_rows = []

        batch_ids = sorted(self.df["batch_id"].unique())

        for batch_id in batch_ids:
            df_batch = self.extract_batch(batch_id)

            ph_mask = self.optimal_ph_mask(df_batch)
            temperature_mask = self.optimal_temperature_mask(df_batch)

            ph_optimal_percent = round(ph_mask.mean() * 100, 2)

            temperature_optimal_percent = round(
                temperature_mask.mean() * 100,
                2
            )

            final_product = df_batch.iloc[-1]["C_product_g_L^-1"]

            summary_rows.append({
                "batch_id": batch_id,
                "ph_optimal_percent": ph_optimal_percent,
                "temperature_optimal_percent": temperature_optimal_percent,
                "C_product_g_L^-1_final": final_product
            })

        df_summary = pd.DataFrame(summary_rows)

        output_directory = os.path.dirname(filepath)

        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        df_summary.to_csv(filepath, index=False)