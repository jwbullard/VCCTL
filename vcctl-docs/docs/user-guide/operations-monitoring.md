# Operations Monitoring

## Overview

The **Operations** panel in VCCTL provides centralized monitoring and management of all running, paused, and completed simulations. Whether you're generating microstructures, running hydration simulations, or calculating elastic moduli, this panel gives you real-time visibility into progress, status, and control over execution.

**Key capabilities:**

- Monitor real-time progress of all operations
- View detailed status and current step information
- Pause and resume long-running simulations
- Cancel operations that are no longer needed
- Delete completed operations and their data
- Track multiple concurrent operations simultaneously

---

## Accessing the Operations Panel

1. Click the **Operations** tab in the left sidebar
2. The panel displays a list of all operations in your workspace
3. Operations are organized chronologically with most recent at top
4. Each row shows key information: name, type, status, progress, and actions

![Operations Panel Overview](../assets/images/screenshots/operations/operations-panel-overview.png)

---

## Understanding the Operations List

Each operation in the list displays comprehensive status information:

### Operation Information Columns

| Column | Description |
|--------|-------------|
| **Name** | Operation name you provided during creation |
| **Type** | Operation type (Microstructure, Hydration, Elastic Moduli) |
| **Status** | Current state (Queued, Running, Paused, Completed, Failed) |
| **Progress** | Completion percentage (0-100%) |
| **Current Step** | Detailed description of current activity |
| **Start Time** | When operation began execution |
| **Actions** | Control buttons (Pause/Resume, Cancel, Delete) |

### Operation Status Indicators

**🔵 Queued** (Blue):
- Operation created but not yet started
- Waiting for system resources or user action
- No computational work being performed

**🟢 Running** (Green):
- Operation actively executing
- Progress updates in real-time
- Current step shows specific activity

![Running Operation](../assets/images/screenshots/operations/operations-running.png)

**🟡 Paused** (Yellow):
- Operation temporarily suspended
- Can be resumed from current state
- No computational resources consumed

![Paused Operation](../assets/images/screenshots/operations/operations-paused.png)

**✅ Completed** (Green checkmark):
- Operation finished successfully
- Results available for viewing
- Ready for deletion if no longer needed

![Completed Operation](../assets/images/screenshots/operations/operations-completed.png)

**❌ Failed** (Red X):
- Operation encountered an error and stopped
- Check logs for error details
- May need parameter adjustment and restart

---

## Monitoring Progress

Real-time progress information helps you understand what each operation is doing and estimate completion time.

### Progress Percentage

The **Progress** column shows overall completion as a percentage:

- **0% to 10%**: Initialization (loading data, setting up)
- **10% to 90%**: Main computation phase
- **90% to 100%**: Finalization (writing output, cleanup)

**Typical Progress Patterns:**

- **Microstructure Generation**: Steady linear progress through particle placement
- **Hydration Simulation**: Progress based on simulation time vs target time
- **Elastic Calculations**: Iterative solver progress through cycles

### Current Step Information

The **Current Step** field provides detailed activity descriptions:

**Microstructure Operations:**
```
Placing particles - 45.2% complete (step 5623/12436)
```

**Hydration Operations:**
```
Simulating hydration at 72.5 hours (target: 168.0 hours) - 43%
```

**Elastic Operations:**
```
Computing elastic moduli - cycle 18/40 (45.0%, gradient: 0.15)
```

![Progress Details](../assets/images/screenshots/operations/operations-progress-details.png)

!!! tip "Estimating Completion Time"
    For linear operations (microstructure, hydration), you can estimate remaining time:

    **Remaining Time ≈ (Elapsed Time / Progress) × (1 - Progress)**

    Example: If 30% complete after 10 minutes, expect ~23 more minutes.

---

## Controlling Operations

Manage operation execution with pause, resume, cancel, and delete actions.

### Pausing Operations

Temporarily suspend an operation to free up system resources or prioritize other work.

**To pause an operation:**

1. Locate a single-click on the running operation in the list
2. Click the **"Pause"** button in the Actions toolbar
3. Status changes to **Paused** (yellow indicator)
4. Operation stops immediately but preserves current state

**When to use pause:**

- Need to run other high-priority simulations
- System running low on memory or CPU
- Want to adjust parameters before continuing (not currently supported - would need restart)
- Need to shut down computer but want to continue later

!!! note "Pause Limitations"
    Pausing saves the current state, but you cannot modify parameters of a paused operation. To change parameters, you must cancel the operation and create a new one with updated settings.

### Resuming Operations

Continue a paused operation from where it left off.

**To resume an operation:**

1. Locate and single-click on the paused operation in the list
2. Click the **"Pause"** button in the Actions toolbar
3. Status changes back to **Running** (green indicator)
4. Computation continues from paused state

**Resume behavior:**

- Microstructure: Continues particle placement
- Hydration: Continues time evolution
- Elastic: Continues iterative solver cycles

### Canceling Operations

Stop an operation permanently if you no longer need the results or want to start over with different parameters.

**To cancel an operation:**

1. Locate and single-click on the running or paused operation
2. Click the **"Cancel/Stop"** button in the Actions toolbar
3. Confirmation dialog appears asking "Are you sure?"
4. Click **"Yes"** to confirm cancellation

**Effects of cancellation:**

- Operation stops immediately
- Partial results are preserved in Operations folder
- Database record remains but marked as canceled
- Cannot resume a canceled operation
- Can delete the operation to remove all data

!!! warning "Cancellation is Permanent"
    Once canceled, an operation cannot be resumed. You would need to create and start a new operation with the same parameters if you want to try again.

### Deleting Operations

Remove completed, failed, or canceled operations from the database and optionally delete their output files.

**To delete an operation:**

1. Locate and single-click on the operation you want to remove
2. Click the **"Delete"** button (trash icon) in the Actions column
3. Confirmation dialog appears

**When to delete:**

- Test operations no longer needed
- Failed operations you won't troubleshoot
- Completed operations you've already archived elsewhere
- Free up disk space by removing large output files

**What gets deleted:**

- Database record (operation metadata, parameters, lineage)
- Operation folder in `Operations/` directory (if selected)
- All output files (microstructures, snapshots, results, logs)

!!! danger "Deletion is Permanent"
    Deleted files cannot be recovered unless you have backups. Export any important data before deleting!

---

## Operation Types and Behaviors

Different operation types have unique monitoring characteristics.

### Microstructure Generation Operations

**Typical Duration:** 2 minutes  to 30 minutes (depends on system size and
particle shape)

**Progress Indicators:**
- Shows particle placement count
- Progress based on total particles to place
- Relatively predictable completion time

**Current Step Examples:**
```
Placing particles - 12.5% (placing C₃S particles)
Placing particles - 45.3% (placing fine aggregate)
Finalizing microstructure - 98.2%
```

**Completion Criteria:**
- All particles successfully placed
- System reaches target volume fractions
- Output files written (`.pimg`, `psd` files)

### Hydration Simulation Operations

**Typical Duration:** 10 minutes to several hours (depends on target time)

**Progress Indicators:**
- Shows current simulation time vs target time
- Progress = (Current Time / Target Time) × 100%
- May slow down at later stages due to densification

**Current Step Examples:**
```
Simulating hydration at 12.5 hours (target: 168.0 hours) - 7.4%
Simulating hydration at 96.3 hours (target: 168.0 hours) - 57.3%
Writing snapshot at 168.0 hours - 100%
```

**Completion Criteria:**
- Simulation reaches target time
- Degree of hydration calculated
- All time snapshots saved
- Output files written

**Special Considerations:**
- Multiple snapshots saved during execution
- Can be very long-running (days for 90+ days simulation)
- Progress may be non-linear (slows at high degrees of hydration)

### Elastic Moduli Calculation Operations

**Typical Duration:** 5 minutes to 15 minutes (depends on microstructure size)

**Progress Indicators:**
- Shows cycle number out of total cycles (typically 40)
- Progress = (Current Cycle / Total Cycles) × 100%
- Includes convergence gradient value

**Current Step Examples:**
```
Computing elastic moduli - cycle 5/40 (12.5%, gradient: 0.45)
Computing elastic moduli - cycle 25/40 (62.5%, gradient: 0.08)
Finalizing calculation - 100%
```

**Completion Criteria:**
- All solver cycles completed
- Convergence achieved (gradient < threshold)
- Effective moduli calculated
- Output files written (EffectiveModuli.csv, strain energy data)

**Convergence Monitoring:**
- Gradient value should decrease over cycles
- Lower gradient = better convergence
- Target gradient typically < 0.05 for good results

---

## Concurrent Operations

VCCTL supports running multiple operations simultaneously with automatic resource management.

### Running Multiple Operations

**To start concurrent operations:**

1. Create and start first operation from any panel
2. Switch to different panel and create second operation
3. Both operations appear in Operations panel
4. System automatically manages CPU and memory allocation

**Recommended Limits:**

- **Microstructure + Hydration**: Both can run concurrently
- **2-3 Hydrations**: If system has sufficient RAM (8+ GB)
- **Elastic + Hydration**: Both are CPU-intensive, may slow each other

!!! warning "System Resources"
    Running too many concurrent operations can:

    - Slow down all operations (CPU contention)
    - Cause memory issues (swapping to disk)
    - Make system unresponsive

    Monitor your system performance and limit concurrent operations accordingly.

### Priority and Resource Management

VCCTL does not currently implement operation priority levels. All operations receive equal CPU time from the operating system's scheduler.

**Best Practices:**

- Start most important operation first
- Pause low-priority operations if system slows
- Run overnight for long hydrations
- Use smaller system sizes for test runs

---

## Troubleshooting

### Operation Stuck at Same Progress

**Symptoms:**
- Progress percentage not changing for extended period
- Current step text not updating

**Possible Causes:**

1. **Long computation phase**: Some operations have phases that take disproportionately long (e.g., elastic convergence)
2. **System resource contention**: Other programs consuming CPU/memory
3. **Disk I/O bottleneck**: Slow disk writing snapshots

**Solutions:**

- Wait longer (some phases genuinely take time)
- Close other applications to free resources
- Check system monitor for CPU/memory usage
- If truly stuck (>1 hour with no progress), cancel and restart

### Operation Failed Unexpectedly

**Symptoms:**
- Status changes to Failed (red X)
- Progress stops

**Common Causes:**

1. **Invalid parameters**: Check console logs for error messages
2. **Insufficient memory**: Operation ran out of RAM
3. **Disk full**: No space to write output files
4. **File permissions**: Cannot write to Operations folder

**Solutions:**

- Review operation parameters before restarting
- Reduce system size if memory issue
- Free up disk space
- Check Operations folder permissions

### Cannot Pause or Resume

**Symptoms:**
- Pause button does nothing
- Resume button grayed out

**Possible Causes:**

1. **Operation in transition**: Status changing between states
2. **Backend process not responding**: Rare but possible

**Solutions:**

- Wait a few seconds and try again
- If persistent, cancel operation and restart
- Restart VCCTL application if problem continues

### Deleted Operation Still Appears

**Symptoms:**
- Deleted operation reappears after refresh
- Database shows operation still exists

**Possible Causes:**

1. **Database sync delay**: Sometimes takes a moment to update
2. **File lock**: Output files still open by viewer

**Solutions:**

- Refresh the operations list manually
- Close any open result viewers for that operation
- Restart VCCTL if issue persists

---

## Best Practices

### Operation Management Strategy

**Organization:**

1. **Use descriptive names**: Include date, mix type, or purpose
   - Good: "TypeI-25C-28day-v2"
   - Poor: "test1", "new", "final"

2. **Document parameters**: Take notes on special settings used

3. **Regular cleanup**: Delete test operations weekly

4. **Archive important results**: Export data before deleting operations

**Monitoring Workflow:**

1. **Start operation**: Configure and launch from appropriate panel
2. **Quick check**: Verify operation appears in Operations panel as Running
3. **Periodic monitoring**: Check progress every 15-30 minutes for long operations
4. **Completion verification**: Confirm Completed status and check results
5. **Cleanup**: Delete operation after archiving results

### Resource Optimization

**For Long Operations (>1 hour):**

- Run overnight or during low-usage periods
- Don't run other intensive programs simultaneously
- Ensure adequate cooling if running on laptop
- Consider using cloud/HPC if available

**For Multiple Operations:**

- Stagger start times by 5-10 minutes
- Monitor system resources (Activity Monitor / Task Manager)
- Prioritize scientifically important over test runs

### Data Management

**Regular Maintenance:**

1. **Weekly**: Delete test and failed operations
2. **Monthly**: Archive completed operations' data to external storage
3. **Before major work**: Clean up old operations to ensure disk space

**Export Strategy:**

- Export critical data immediately after completion
- Keep exported CSVs organized by project/date
- Document which operations correspond to which data files

---

## Understanding Operation Lineage

VCCTL automatically tracks relationships between operations, creating a lineage chain.

### Parent-Child Relationships

**Microstructure → Hydration:**

- Microstructure is parent
- Hydration is child
- Hydration stored in nested folder: `Operations/MicrostructureName/HydrationName/`

**Hydration → Elastic:**

- Hydration is parent
- Elastic is child
- Elastic stored in nested folder: `Operations/HydrationName/ElasticName/`

### Viewing Lineage

The Operations panel shows nested structure:

```
📁 Microstructure: TypeI-Paste-100x100x100
  📁 Hydration: HY-TypeI-25C-28day
    📄 Elastic: Elastic-HY-TypeI-Final
    📄 Elastic: Elastic-HY-TypeI-7day
```

**Benefits of Lineage:**

- Automatically organizes related operations
- Preserves parameter inheritance
- Makes it easy to trace workflow
- Simplifies data management

### Deleting Parent Operations

**Warning:** Deleting a parent operation can affect children.

**Options when deleting parent:**

1. **Delete parent only**: Children remain but lose context
2. **Delete parent and all children**: Entire lineage removed
3. **Delete parent but keep children**: Must manually move child folders

!!! danger "Cascade Deletion"
    If you choose "Delete database record and files" for a parent operation, all child operations and their files will also be deleted. This cannot be undone!

---

## Advanced Features

### Filtering and Searching

While not currently implemented in the UI, you can manually search operations:

**By Name:** Scroll through list or use browser's find function (Ctrl+F / Cmd+F)

**By Type:** Look for type column indicators

**By Status:** Group visually by color-coded status indicators

### Exporting Operation Information

To create a summary of all operations:

1. View Operations panel
2. Take screenshot or manually record operation details
3. Export results data from each operation individually via Results panel

**Future Enhancement Opportunity:** Batch export of operation metadata to CSV for record-keeping.

### Log Files

Each operation generates log files in its folder:

**Location:** `Operations/[OperationName]/console_output.txt`

**Contents:**
- Detailed execution log
- Parameter values used
- Warning and error messages
- Timing information
- Debug output (if enabled)

**Accessing Logs:**

1. Navigate to Operations folder in file browser
2. Open operation subfolder
3. View `console_output.txt` with text editor

**When to Check Logs:**

- Operation failed unexpectedly
- Results seem incorrect
- Need to debug parameters
- Report issues to developers

---

## Summary

The Operations Monitoring panel provides:

- ✅ Real-time visibility into all running simulations
- ✅ Progress tracking with detailed status information
- ✅ Control over execution (pause, resume, cancel)
- ✅ Organization of multiple concurrent operations
- ✅ Management of completed operations and data
- ✅ Automatic lineage tracking for related operations

These capabilities enable you to:

- **Monitor** multiple operations efficiently
- **Control** computational resources effectively
- **Manage** workflow and data organization
- **Troubleshoot** problems quickly
- **Optimize** system performance

!!! success "Workflow Integration"
    The Operations panel integrates with all other VCCTL panels:

    - Start operations from Materials, Mix Design, Hydration, or Elastic panels
    - Monitor progress here in Operations panel
    - View results through Results panel
    - Complete workflow: Create → Monitor → Analyze

---

## Quick Reference

### Common Actions

| Action | Steps |
|--------|-------|
| Check progress | View Progress column percentage and Current Step text |
| Pause operation | Click Pause button in Actions column |
| Resume operation | Click Resume button for paused operation |
| Cancel operation | Click Cancel → Confirm with Yes |
| Delete operation | Click Delete → Choose record only or record+files |
| View results | Switch to Results panel, select completed operation |

### Status Meanings

| Status | Meaning | Actions Available |
|--------|---------|-------------------|
| Queued | Not started | Cancel, Delete |
| Running | Currently executing | Pause, Cancel |
| Paused | Temporarily stopped | Resume, Cancel, Delete |
| Completed | Finished successfully | Delete, View Results |
| Failed | Error occurred | Delete, Check Logs |

### Typical Operation Durations

| Operation Type | System Size | Typical Duration |
|----------------|-------------|------------------|
| Microstructure | 100³ voxels | 2-5 minutes |
| Microstructure | 200³ voxels | 10-20 minutes |
| Hydration | 7 days | 15-30 minutes |
| Hydration | 28 days | 1-2 hours |
| Hydration | 90 days | 3-6 hours |
| Elastic | Any size | 5-15 minutes |

!!! note "Duration Variability"
    Actual durations depend on:
    - CPU speed and core count
    - Available RAM
    - Disk I/O speed
    - Number of concurrent operations
    - Mix complexity (number of components)
