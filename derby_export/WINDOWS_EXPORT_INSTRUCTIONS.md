# Derby Database Export Instructions for Windows

## Prerequisites
- Your VCCTL application should be completely closed
- You should have access to the Derby installation at `db-derby-10.5.3.0-bin`
- The Derby databases are located at the path you provided

## Step 1: Open Command Prompt
1. Press `Win + R`, type `cmd`, and press Enter
2. Navigate to your Derby installation directory:
   ```cmd
   cd C:\path\to\your\db-derby-10.5.3.0-bin\bin
   ```

## Step 2: Set Environment Variables
```cmd
set DERBY_HOME=C:\path\to\your\db-derby-10.5.3.0-bin
set CLASSPATH=%DERBY_HOME%\lib\derby.jar;%DERBY_HOME%\lib\derbytools.jar
```

## Step 3: Start Derby ij Tool
```cmd
java org.apache.derby.tools.ij
```

## Step 4: Export Commands
Copy and paste these commands one by one into the ij tool:

### Export Cement Database
```sql
CONNECT 'jdbc:derby:C:\path\to\your\VCCTL\data\database\vcctl_cement';

CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'AGGREGATE', 'C:\temp\aggregate.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'AGGREGATE_SIEVE', 'C:\temp\aggregate_sieve.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'CEMENT', 'C:\temp\cement.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'FLY_ASH', 'C:\temp\fly_ash.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'SLAG', 'C:\temp\slag.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'INERT_FILLER', 'C:\temp\inert_filler.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'GRADING', 'C:\temp\grading.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'PARTICLE_SHAPE_SET', 'C:\temp\particle_shape_set.csv', null, null, null);
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'DB_FILE', 'C:\temp\db_file.csv', null, null, null);

DISCONNECT;
```

### Export Operation Database
```sql
CONNECT 'jdbc:derby:C:\path\to\your\VCCTL\data\database\vcctl_operation';

CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'OPERATION', 'C:\temp\operation.csv', null, null, null);

DISCONNECT;
```

### Export User Database
```sql
CONNECT 'jdbc:derby:C:\path\to\your\VCCTL\data\database\vcctl_user';

CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'USER_DATA', 'C:\temp\user_data.csv', null, null, null);

DISCONNECT;
```

### Exit ij Tool
```sql
exit;
```

## Step 5: Transfer Files
After successful export, you should have these CSV files in `C:\temp\`:
- aggregate.csv
- aggregate_sieve.csv
- cement.csv
- fly_ash.csv
- slag.csv
- inert_filler.csv
- grading.csv
- particle_shape_set.csv
- db_file.csv
- operation.csv
- user_data.csv

Transfer these files to your Mac system in the directory:
`/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/`

## Notes
- Replace `C:\path\to\your\` with your actual paths
- Make sure the `C:\temp\` directory exists, or change to another directory you prefer
- If you get permission errors, try running Command Prompt as Administrator
- If a table doesn't exist, you'll get an error but other exports will continue
- Each CONNECT command should show "ij>" prompt before running the CALL commands

## Troubleshooting
- If you get "database already in use" errors, make sure your VCCTL application is completely closed
- If you get "table does not exist" errors, that's normal - not all databases may have all tables
- If export fails, check that the output directory exists and is writable

Once you have the CSV files on your Mac, I can import them into the SQLite database.