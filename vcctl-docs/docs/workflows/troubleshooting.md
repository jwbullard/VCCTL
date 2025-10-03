# Troubleshooting Guide

This comprehensive troubleshooting guide consolidates common issues and solutions from all VCCTL operations. Issues are organized by workflow area for easy reference.

---

## Materials Management

### Cannot Create or Edit Materials

**Error: "Material name already exists"**:

- Material names must be unique within each type
- Try adding a version number or date to the name (e.g., "TypeI-Cement-v2")
- Delete the existing material if you want to reuse the name

**PSD (Particle Size Distribution) errors**:

- Ensure cumulative passing values are between 0-100%
- Values must increase monotonically (each value ≥ previous value)
- Include at least 3 data points for valid PSD
- Check that sieve sizes are in micrometers (μm)

### Material Import Fails

**Invalid file format**:

- Supported formats: JSON, CSV
- Check file encoding (should be UTF-8)
- Verify JSON syntax is valid (no trailing commas, proper quotes)
- CSV files should have headers in first row

**Missing required fields**:

- Cement materials require: name, density, chemical composition (oxide percentages)
- Aggregates require: name, density, PSD data
- SCMs require: name, density, type, chemical composition

### Validation Warnings

**Cement composition doesn't sum to 100%**:

- Check that all oxide percentages (SiO₂, Al₂O₃, Fe₂O₃, CaO, MgO, SO₃, etc.) sum to ~100% (±2%)
- Use normalized values if working from non-normalized data
- Missing oxides should be set to 0%, not left blank

**Unrealistic density values**:

- Typical Portland cement: 3.10-3.20 g/cm³
- Aggregates: 2.60-2.80 g/cm³ (silica/limestone), up to 3.0 g/cm³ (dense aggregates)
- Fly ash: 2.2-2.4 g/cm³
- Slag: 2.85-2.95 g/cm³
- Silica fume: 2.2-2.3 g/cm³

---

## Mix Design

### Mix Validation Fails

**Water-binder ratio out of range**:

- Practical range: 0.25-0.70
- Very low w/b (<0.30): May have workability issues
- Very high w/b (>0.60): Poor strength and durability
- Adjust water content or binder content to achieve target

**Component volume fractions don't sum to 1.0**:

- Total volume fractions should equal 100% (allowing for air content)
- Check that all materials have correct densities
- Verify mass inputs are in consistent units
- Air content typically 1-8% for normal concrete

**Aggregate grading issues**:

- Fine/coarse aggregate ratio typically 35:65 to 45:55
- Ensure gradation curves are smooth (no gaps or sudden jumps)
- Total aggregate content typically 60-75% by volume

### Microstructure Generation Fails

**System size too large**:

- Maximum recommended: 200×200×200 voxels
- Larger systems require significant RAM (>16 GB)
- Start with 100×100×100 for testing
- Use 1.0 μm/voxel resolution currently

**Particle placement fails**:

- Volume fractions may be too high for successful packing
- Reduce total solid content slightly (increase w/c ratio)
- Check that aggregate sizes are appropriate for system size
- Very large particles may not fit in small systems

**Operation shows "Failed" status**:

- Check Operations panel for detailed error message
- Review console_output.txt in operation folder for full log
- Common causes: Memory exhaustion, invalid PSD data, file permission issues

---

## Hydration Simulation

### Simulation Won't Start

**No microstructure selected**:

- Must select an initial microstructure from dropdown
- Microstructure must be from a completed Mix Design operation
- If dropdown is empty, create a mix design first

**Invalid simulation parameters**:

- Target simulation time must be > 0
- Temperature must be reasonable (5-60°C)
- Time step size should be appropriate for kinetics
- Check that all required fields have values

### Simulation Runs Very Slowly

**Large system size**:

- Hydration time scales with system volume
- 100×100×100 system: ~30-60 minutes for 28 days
- 200×200×200 system: Several hours for 28 days
- Consider smaller system for parameter studies

**High target time**:

- Hydration to 90+ days can take many hours
- Most property development occurs in first 28 days
- Use shorter times for initial testing
- Run long simulations overnight

### Unrealistic Hydration Results

**Degree of hydration too high/low**:

- Check w/c ratio is realistic (0.3-0.6 typical)
- Verify cement composition is correct
- Temperature affects hydration rate significantly
- Time conversion factor may need adjustment (default: 0.00035)

**Heat evolution doesn't match experiments**:

- Adjust time calibration parameters
- Check cement composition matches experimental cement
- Verify activation energies are appropriate
- Temperature profile should match experimental conditions

---

## Elastic Calculations

### Calculation Fails to Start

**No microstructures available**:

- Ensure you've completed a hydration simulation first
- Check that hydration operation generated snapshots
- Verify Operations folder contains hydration results

**Missing aggregate properties**:

- If calculation requires aggregates, all properties must be specified
- Use default values if unsure (bulk: 37 GPa, shear: 29 GPa)

### Calculation Doesn't Complete

**Slow convergence**:

- Check progress panel for gradient values
- If gradient not decreasing, microstructure may have issues
- Try with different microstructure snapshot

**Memory issues**:

- Large microstructures (>200×200×200) may require significant RAM
- Consider using smaller system sizes in mix design

### Unrealistic Results

**Elastic modulus too high or too low**:

- Verify aggregate elastic properties are reasonable
- Check that microstructure hydration reached expected degree
- Ensure proper units (GPa for moduli)
- Typical mature paste: 18-25 GPa; with aggregates: 25-40 GPa

**ITZ analysis shows no variation**:

- Requires aggregates in mix design
- ITZ effects may be subtle at early ages
- Ensure sufficient spatial resolution in microstructure

---

## Results Visualization

### 3D Viewer Issues

**Viewer opens but shows black/blank screen**:

- Check that operation completed successfully
- Verify microstructure files exist in Operations folder
- Try restarting VCCTL to refresh PyVista backend

**Slow rendering performance**:

- Switch to isosurface mode (faster than volume rendering)
- Hide unnecessary phases to reduce complexity
- Disable cross-section planes when not needed
- Close other open viewers
- Consider smaller system sizes in future simulations

**Phase colors all look similar**:

- Click color swatches in phase controls
- Choose more contrasting colors manually
- Use colorblind-friendly palettes for accessibility

### Plot Display Issues

**"No data available for plotting"**:

- Ensure hydration simulation saved time-series output
- Check that simulation ran to completion
- Verify progress.json or output files exist in operation folder

**Plot appears but shows unexpected values**:

- Verify time units match expectations (hours vs days)
- Check that degree of hydration is between 0 and 1
- Compare heat values to typical Portland cement (300-400 J/g total)

### Export Problems

**Export button does not work**:

- Check disk space availability
- Verify write permissions for output directory
- Try exporting to different location (Desktop, Documents)
- Check for special characters in filename

**Exported data appears corrupted**:

- Ensure operation completed fully before exporting
- Try different export format (CSV vs JSON)
- Check that files aren't locked by other applications

---

## Operations Monitoring

### Operation Stuck at Same Progress

**Symptoms**: Progress percentage not changing for extended period, current step text not updating

**Possible Causes**:

1. **Long computation phase**: Some operations have phases that take disproportionately long (e.g., elastic convergence)
2. **System resource contention**: Other programs consuming CPU/memory
3. **Disk I/O bottleneck**: Slow disk writing snapshots

**Solutions**:

- Wait longer (some phases genuinely take time)
- Close other applications to free resources
- Check system monitor for CPU/memory usage
- If truly stuck (>1 hour with no progress), cancel and restart

### Operation Failed Unexpectedly

**Symptoms**: Status changes to Failed (red X), progress stops

**Common Causes**:

1. **Invalid parameters**: Check console logs for error messages
2. **Insufficient memory**: Operation ran out of RAM
3. **Disk full**: No space to write output files
4. **File permissions**: Cannot write to Operations folder

**Solutions**:

- Review operation parameters before restarting
- Reduce system size if memory issue
- Free up disk space (need several GB for large operations)
- Check Operations folder permissions (should be read/write)

### Cannot Pause or Resume

**Symptoms**: Pause button does nothing, Resume button grayed out

**Possible Causes**:

1. **Operation in transition**: Status changing between states
2. **Backend process not responding**: Rare but possible

**Solutions**:

- Wait a few seconds and try again
- If persistent, cancel operation and restart
- Restart VCCTL application if problem continues

### Deleted Operation Still Appears

**Symptoms**: Deleted operation reappears after refresh, database shows operation still exists

**Possible Causes**:

1. **Database sync delay**: Sometimes takes a moment to update
2. **File lock**: Output files still open by viewer

**Solutions**:

- Refresh the operations list manually
- Close any open result viewers for that operation
- Restart VCCTL if issue persists

---

## General System Issues

### Application Won't Start

**"Module not found" errors**:

- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version (requires Python 3.8+)

**GTK initialization errors**:

- Ensure GTK 3.0 is installed on your system
- macOS: `brew install gtk+3`
- Linux: `sudo apt-get install python3-gi gir1.2-gtk-3.0`
- Windows: Use MSYS2/GTK installer

### UI Responsiveness Issues

**Application becomes slow or unresponsive**:

- Close unused panels or dialogs
- Limit number of concurrent operations
- Restart application periodically for long sessions
- Check system resources (Activity Monitor/Task Manager)

### Database Errors

**"Database is locked" messages**:

- Another VCCTL instance may be running
- Close all VCCTL windows and restart
- Check for orphaned Python processes
- Worst case: backup and delete `vcctl.db-wal` file

**Corrupted database**:

- Backup current database: `cp vcctl.db vcctl.db.backup`
- Try database repair (contact support for tools)
- If necessary, start fresh (will lose saved operations)

### File I/O Errors

**Cannot read/write files**:

- Check disk space (need several GB free)
- Verify folder permissions
- Ensure antivirus isn't blocking VCCTL
- Check file paths for special characters or spaces

**Missing operation files**:

- Verify Operations folder exists and is writable
- Check that operations completed successfully
- May need to regenerate from saved parameters
- Use File Manager panel to investigate

---

## Performance Optimization Tips

### Reducing Simulation Time

1. **Use smaller system sizes**: 100×100×100 instead of 200×200×200
2. **Limit target simulation time**: Focus on critical time points (1d, 7d, 28d)
3. **Reduce snapshot frequency**: Fewer snapshots = faster hydration
4. **Run overnight**: Schedule long operations during off-hours
5. **Close other applications**: Free up CPU and memory

### Managing Memory Usage

1. **Monitor system resources**: Check RAM usage during operations
2. **Limit concurrent operations**: Run 1-2 at a time max
3. **Close result viewers**: Free memory after viewing
4. **Restart periodically**: Clear accumulated memory
5. **Upgrade RAM**: 16+ GB recommended for large systems

### Disk Space Management

1. **Clean old operations**: Delete test runs regularly
2. **Export important data**: Then delete operations
3. **Archive to external drive**: Move completed work off main disk
4. **Monitor Operations folder**: Can grow to tens of GB

---

## Getting Additional Help

If problems persist after trying these solutions:

1. **Check error logs**:
   - Application log: `logs/vcctl.log`
   - Operation logs: `Operations/[operation-name]/console_output.txt`

2. **Document the issue**:
   - Steps to reproduce
   - Error messages
   - System specifications
   - VCCTL version

3. **Gather diagnostic information**:
   - Screenshot of error
   - Relevant operation parameters
   - System information (OS, RAM, Python version)

4. **Contact support**:
   - GitHub Issues: [github.com/jwbullard/VCCTL/issues](https://github.com/jwbullard/VCCTL/issues)
   - Email: jeff.bullard@tamu.edu
   - Include all diagnostic information from above

---

## Quick Reference

### Common Error Messages

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| "Material name already exists" | Duplicate name | Use unique name with version/date |
| "Composition does not sum to 100%" | Invalid oxide %s | Check all oxides sum to ~100% |
| "No microstructure selected" | Missing input | Create/select mix design first |
| "Operation failed to start" | Invalid parameters | Review all parameter values |
| "Out of memory" | System RAM exhausted | Use smaller system size |
| "Disk full" | No space for output | Free up disk space |
| "Database is locked" | Concurrent access | Close other VCCTL instances |
| "Cannot write to folder" | Permission issue | Check folder permissions |

### Typical Value Ranges

| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| Water-cement ratio | 0.30 - 0.65 | Lower = stronger, less workable |
| System size | 50³ - 200³ voxels | Larger = more accurate, slower |
| Resolution | 1.0 μm/voxel | Current standard |
| Cement density | 3.10 - 3.20 g/cm³ | Portland cement typical |
| Aggregate density | 2.60 - 2.80 g/cm³ | Silica/limestone typical |
| Target hydration time | 1 - 90 days | 28 days common reference |
| Elastic modulus (paste) | 18 - 25 GPa | At 28 days, w/c=0.40 |
| Elastic modulus (concrete) | 25 - 40 GPa | With aggregates |
| Degree of hydration (28d) | 0.70 - 0.85 | Depends on w/c ratio |
