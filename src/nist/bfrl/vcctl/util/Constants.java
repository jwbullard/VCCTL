/*
 * Constants.java
 *
 * Created on April 24, 2007, 4:54 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.util;

/**
 *
 * @author mscialom
 */
public interface Constants {
    
    /* VCCTL directories */
    public static final String BIN_DIRECTORY_NAME = "bin";
    public static final String DATA_DIRECTORY_NAME = "data";
    public static final String SRC_DIRECTORY_NAME = "src";
    public static final String USER_DIRECTORY_NAME = "usr";
    public static final String PARTICLE_SHAPE_SET_DIRECTORY_NAME = "particle_shape_set";
    public static final String AGGREGATE_DIRECTORY_NAME = "aggregate";
    public static final String AGGREGATE_FILES_DIRECTORY_NAME = "AggregateFiles";
    public static final String ELASTIC_AGGREGATE_DIRECTORY = "Elastic-moduli-of-aggregate";
    public static final String DATABASE_DIRECTORY_NAME = "database";
    
    public static final String VCCTL_PROFILE_FILE_NAME = ".vcctl_profile";
    
    /* Microstructure */
    public static final double WATER_DENSITY = 0.997;
    public static final double CEMENT_DEFAULT_SPECIFIC_GRAVITY = 3.2;
    public static final double C3S_SPECIFIC_GRAVITY = 3.21;
    public static final double C2S_SPECIFIC_GRAVITY = 3.28;
    public static final double C3A_SPECIFIC_GRAVITY = 3.038;
    public static final double ORTHORHOMBIC_C3A_SPECIFIC_GRAVITY = 3.052;
    public static final double C4AF_SPECIFIC_GRAVITY = 3.73;
    public static final double K2SO4_SPECIFIC_GRAVITY = 2.662;
    public static final double NA2SO4_SPECIFIC_GRAVITY = 2.68;
    public static final double SILICA_FUME_SPECIFIC_GRAVITY = 2.2;
    public static final double CACO3_SPECIFIC_GRAVITY = 2.71;
    public static final double FREE_LIME_SPECIFIC_GRAVITY = 3.31;
    public static final double FLY_ASH_DEFAULT_SPECIFIC_GRAVITY = 2.77;
    public static final double INERT_FILLER_DEFAULT_SPECIFIC_GRAVITY  = 3.00;
    // public static final double INERT_FILLER_DEFAULT_SPECIFIC_GRAVITY  = 2.2;
    public static final double DIHYDRATE_SPECIFIC_GRAVITY = 2.32;
    public static final double HEMIHYDRATE_SPECIFIC_GRAVITY = 2.74;
    public static final double ANHYDRITE_SPECIFIC_GRAVITY = 2.61;
    // public static final double MAX_SIZE_TO_SYSTEM_RATIO = 0.7;
    public static final double EPSILON = 0.001;
    public static final double DEFAULT_AIR_VOLUME_FRACTION = 0.04;
    public static final double SIZE_SAFETY_COEFFICIENT = 1.0/3.0;
    public static final double RESOLUTION_SAFETY_COEFFICIENT = 3.0;
    public static final double DEFAULT_BINDER_SYSTEM_RESOLUTION = 1.0;
    public static final double DEFAULT_CONCRETE_SYSTEM_RESOLUTION = 1.0;
    public static final int DEFAULT_BINDER_SYSTEM_DIMENSION = 100;
    public static final int DEFAULT_CONCRETE_SYSTEM_DIMENSION = 100;
    public static final String DEFAULT_CEMENT = "cement140";
    public static final String DEFAULT_COARSE_GRADING = "MyCoarseGrading";
    public static final int COARSE_AGGREGATE_TYPE = 1;
    public static final int FINE_AGGREGATE_TYPE = 0;
    public static final String DEFAULT_FINE_GRADING = "MyFineGrading";
    public static final String DEFAULT_PARTICLE_SHAPE_SET = "None";
    public static final String COARSE_AGGREGATE_GRADING_NAME_01 = "CoarseAggregateGrading01.gdg";
    public static final String COARSE_AGGREGATE_GRADING_NAME_02 = "CoarseAggregateGrading02.gdg";
    public static final String FINE_AGGREGATE_GRADING_NAME_01 = "FineAggregateGrading01.gdg";
    public static final String FINE_AGGREGATE_GRADING_NAME_02 = "FineAggregateGrading02.gdg";
    
    public static final String DEFAULT_PSD = "cement140 psd";
    
    /* Slag */
    public static final double SLAG_DEFAULT_REACTIONS_ACTIVATION_ENERGY = 50.0;
    public static final double SLAG_DEFAULT_SPECIFIC_GRAVITY = 2.87;
    public static final double SLAG_DEFAULT_MOLECULAR_MASS = 2492.4;
    public static final double SLAG_DEFAULT_CA_SI_MOLAR_RATIO = 0.97;
    public static final double SLAG_DEFAULT_SI_PER_MOLE = 17.0;
    public static final double BASE_SLAG_DEFAULT_REACTIVITY = 1.0;
    public static final double SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_MOLECULAR_MASS = 4307.085;
    public static final double SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_DENSITY = 2.35;
    public static final double SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_CA_SI_MOLAR_RATIO = 1.25;
    public static final double SLAG_GEL_HYDRATION_PRODUCT_DEFAULT_H20_SI_MOLAR_RATIO = 5.059;
    
    /* Aggregate */
    public static final String AGGREGATE_IMAGE_FILE_NAME = "Aggregate.img";
    public static final String AGGREGATE_STATS_FILE_NAME = "Aggregate.stt";
    public static final String GENAGGPACK_INPUT_FILE = "aggpack.in";
    public static final String GENAGGPACK_OUTPUT_FILE = "aggpack.out";
    
    /* Hydration */
    public static final int DEFAULT_HYDRATION_CYCLES_NUMBER = 2000;
    public static final double DEFAULT_DAYS_HYDRATION_TIME = 28.0;
    public static final double DEFAULT_INITIAL_TEMPERATURE = 25.0;
    public static final double DEFAULT_AMBIENT_TEMPERATURE = 25.0;
    public static final double DEFAULT_HEAT_TRANSFER_COEFFICIENT = 0.0;
    public static final double DEFAULT_TIME_CONVERSION_FACTOR = 0.00035;
    public static final double DEFAULT_CEMENT_HYDRATION_ACTIVATION_ENERGY = 40.0;
    public static final double DEFAULT_POZZOLANIC_REACTIONS_ACTIVATION_ENERGY = 83.14;
    public static final double DEFAULT_INDIVIDUAL_PARTICLE_HYDRATION_TIMES_EVALUATION_PERIOD = 1000.0;
    public static final double DEFAULT_PERCOLATION_POROSITY_TIMES_EVALUATION_PERIOD = 1.0;
    public static final double DEFAULT_PERCOLATION_SOLID_TIMES_EVALUATION_PERIOD = 0.5;
    public static final double DEFAULT_OUTPUT_MICROSTRUCTURE_TIMES_PERIOD = 72.0;
    // public static final String PARAMETERS_FILES_DIRECTORY_NAME = "parameters_files";
    // public static final String ALKALI_FILES_DIRECTORY_NAME = "alkali_files";
    // public static final String SLAG_CHARACTERISTICS_FILES_DIRECTORY_NAME = "slag_characteristics_files";
    public static final String DEFAULT_CEMENT_ALKALI_CHARACTERISTICS_FILE = "lowalkali";
    public static final String DEFAULT_FLY_ASH_ALKALI_CHARACTERISTICS_FILE = "alkaliflyash";
    public static final String DEFAULT_SLAG_CHARACTERISTICS_FILE = "slagone";
    public static final String DEFAULT_PARAMETER_FILE = "DefaultParametersFile";
    public static final String DEFAULT_CALORIMETRY_FILE = "DefaultCalorimetryFile";
    public static final String DEFAULT_CHEMICAL_SHRINKAGE_FILE = "DefaultChemicalShrinkageFile";
    public static final String DEFAULT_TIMING_OUTPUT_FILE = "DefaultTimingOutput";
    public static final String NO_FLY_ASH_ALKALI_CHARACTERISTICS_FILE = "alkaliflyash";
    public static final String NO_SLAG_CHARACTERISTICS_FILE = "slagone"; // check if it's correct
    public static final String CEMENT_ALKALI_CHARACTERISTICS_FILE = "alkalichar.dat";
    public static final String FLY_ASH_ALKALI_CHARACTERISTICS_FILE = "alkaliflyash.dat";
    public static final String SLAG_CHARACTERISTICS_FILE = "slagchar.dat";
    public static final String PARAMETER_FILE = "parameter_file.prm";
    public static final String CALORIMETRY_FILE = "calorimetry.heat";
    public static final String CEMENT_PSD_FILE = "cement_psd.psd";
    public static final String CHEMICAL_SHRINKAGE_FILE = "chemical_shrinkage.chs";
    public static final String TIMING_OUTPUT_FILE = "customoutput.dat";
    public static final String IMAGES_LIST_FILENAME = "image_index.txt";
    public static final String TIME_AGING_MODE = "time";
    public static final String CALORIMETRY_AGING_MODE = "calorimetry";
    public static final String CHEMICAL_SHRINKAGE_AGING_MODE = "chemical_shrinkage";
    public static final String DEFAULT_AGING_MODE = TIME_AGING_MODE;
    
    /* Elasticity */
    public static final String ELASTIC_OPERATION_NAME_ROOT = "Elastic-moduli-";
    public static final String EFFECTIVE_MODULI_FILE_NAME = "EffectiveModuli.dat";
    public static final String PHASE_CONTRIBUTIONS_FILE_NAME = "PhaseContributions.dat";
    public static final String ITZ_MODULI_FILE_NAME = "ITZModuli.dat";
    public static final String CONCRETE_MODULI_FILE_NAME = "Concrete.dat";
    public static final String ELASTIC_INPUT_FILE = "elastic.in";
    public static final String ELASTIC_OUTPUT_FILE = "elastic.out";

    /* Transport */
    public static final String TRANSPORT_OPERATION_NAME_ROOT = "Transport-factor-";
    public static final String TRANSPORT_FACTOR_MAJOROUTPUT_FILE_NAME = "TransportFactorOutput.dat";
    public static final String TRANSPORT_FACTOR_RESULTS_FILE_NAME = "TransportFactorResults.dat";
    public static final String TRANSPORT_FACTOR_ITZ_FILE_NAME = "ITZConductivity.dat";
    public static final String TRANSPORT_FACTOR_PHASE_CONTRIBUTIONS_FILE_NAME = "PhaseContributions.dat";
    public static final String TRANSPORT_FACTOR_INPUT_FILE = "transport.in";
    public static final String TRANSPORT_FACTOR_OUTPUT_FILE = "transport.out";
    
    /* Simulation */
    public static final int MAXIMUM_RUNNING_OPERATIONS = 50;
    
    /* Operation types */
    public static final String HYDRATION_OPERATION_TYPE = "Hydration";
    public static final String MICROSTUCTURE_OPERATION_TYPE = "Microstructure";
    public static final String ELASTIC_MODULI_OPERATION_TYPE = "Elastic-moduli";
    public static final String TRANSPORT_FACTOR_OPERATION_TYPE = "Transport-factor";
    public static final String AGGREGATE_OPERATION_TYPE = "Aggregate";
    
    /* Operation status */
    public static final String OPERATION_FINISHED_STATUS = "finished";
    public static final String OPERATION_QUEUED_STATUS = "queued";
    public static final String OPERATION_CANCELLED_STATUS = "cancelled";
    public static final String OPERATION_RUNNING_STATUS = "running";
    public static final String OPERATION_ERROR_STATUS = "error";
    
    /* Tables names */
    public static final String AGGREGATE_TABLE_NAME = "aggregate";
    public static final String CEMENT_TABLE_NAME = "cement";
    public static final String DB_FILE_TABLE_NAME = "db_file";
    public static final String FLY_ASH_TABLE_NAME = "flyash";
    public static final String GRADING_TABLE_NAME = "grading";
    public static final String INERT_FILLER_TABLE_NAME = "inert_filler";
    public static final String PASRTICLE_SHAPE_SET_TABLE_NAME = "particle_shape_set";
    public static final String SLAG_TABLE_NAME = "slag";
    public static final String OPERATION_TABLE_NAME = "operation";
    public static final String PROFILE_TABLE_NAME = "profile";
    public static final String USER_TABLE_NAME = "userdata";
    
    /* Cement database */
    public static final String ALKALI_CHARACTERISTICS_TYPE = "alkali_characteristics";
    public static final String SLAG_CHARACTERISTICS_TYPE = "slag_characteristics";
    public static final String PARAMETER_FILE_TYPE = "parameter_file";
    public static final String CALORIMETRY_FILE_TYPE = "calorimetry_file";
    public static final String CHEMICAL_SHRINKAGE_FILE_TYPE = "chemical_shrinkage_file";
    public static final String TIMING_OUTPUT_FILE_TYPE = "timing_output_file";
    public static final String PSD_TYPE = "psd";
    
    /* Errors types */
    public static final String NO_DATA_OF_THIS_TYPE = "No data of this type";
    public static final String NO_DATA_FOR_THIS_NAME = "No data for this name";
    public static final String EMPTY_ARGUMENT = "The argument is empty";
    public static final String ARGUMENT_VALUE_NOT_ALLOWED = "The value for this argument is not allowed";
    public static final int ER_DUP_ENTRY = 1062;

    /** Line style: line */
    public static final String STYLE_LINE = "line";
    /** Line style: dashed */
    public static final String STYLE_DASH = "dash";
    /** Line style: dotted */
    public static final String STYLE_DOT = "dot";
}
