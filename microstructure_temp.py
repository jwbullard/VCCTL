    def _load_default_parameters(self) -> None:
        """Load default parameters - simplified for preview-only mode."""
        self._update_status("Ready - parameters configured in Mix Design tool")
    
    def _update_status(self, message: str) -> None:
        """Update status message."""
        self.status_label.set_text(message)
    
    def _get_parameters_from_mix_design(self) -> Optional[MicrostructureParams]:
        """Get parameters from Mix Design tool (placeholder for future integration)."""
        # TODO: Implement communication with Mix Design tool to get current parameters
        # For now, return default parameters
        return MicrostructureParams(
            system_size=100,
            resolution=1.0,
            water_binder_ratio=0.4,
            aggregate_volume_fraction=0.7,
            air_content=0.05,
            cement_shape_set="default",
            aggregate_shape_set="default",
            enable_flocculation=False,
            flocculation_degree=0.0,
            random_seed=0
        )