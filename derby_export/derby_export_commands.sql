-- Derby Database Export Commands
-- Run these commands in Derby ij tool

-- Connect to cement database
CONNECT 'jdbc:derby:/Users/jwbullard/Documents/Projects/Modeling/VCCTL/data/database/vcctl_cement';

-- Export AGGREGATE table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'AGGREGATE', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/aggregate.csv', null, null, null);

-- Export AGGREGATE_SIEVE table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'AGGREGATE_SIEVE', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/aggregate_sieve.csv', null, null, null);

-- Export CEMENT table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'CEMENT', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/cement.csv', null, null, null);

-- Export FLY_ASH table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'FLY_ASH', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/fly_ash.csv', null, null, null);

-- Export SLAG table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'SLAG', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/slag.csv', null, null, null);

-- Export INERT_FILLER table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'INERT_FILLER', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/inert_filler.csv', null, null, null);

-- Export GRADING table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'GRADING', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/grading.csv', null, null, null);

-- Export PARTICLE_SHAPE_SET table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'PARTICLE_SHAPE_SET', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/particle_shape_set.csv', null, null, null);

-- Export DB_FILE table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'DB_FILE', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/db_file.csv', null, null, null);

DISCONNECT;

-- Connect to operation database
CONNECT 'jdbc:derby:/Users/jwbullard/Documents/Projects/Modeling/VCCTL/data/database/vcctl_operation';

-- Export OPERATION table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'OPERATION', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/operation.csv', null, null, null);

DISCONNECT;

-- Connect to user database
CONNECT 'jdbc:derby:/Users/jwbullard/Documents/Projects/Modeling/VCCTL/data/database/vcctl_user';

-- Export USER_DATA table
CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', 'USER_DATA', '/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_export/user_data.csv', null, null, null);

DISCONNECT;

