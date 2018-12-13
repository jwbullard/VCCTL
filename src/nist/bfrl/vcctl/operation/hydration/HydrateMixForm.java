/*
 * HydrateMixForm.java
 *
 * Created on August 23, 2005, 10:56 AM
 */

package nist.bfrl.vcctl.operation.hydration;

import java.io.File;
import java.sql.SQLException;
import javax.servlet.http.HttpServletRequest;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.CementDatabase;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.*;
import nist.bfrl.vcctl.operation.microstructure.GenerateMicrostructureForm;
import nist.bfrl.vcctl.operation.microstructure.Phase;
import org.apache.struts.action.*;

import java.util.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.*;

/**
 *
 * @author tahall
 */
public class HydrateMixForm extends ActionForm {
    
    public void init(String userName) throws NullMicrostructureException, NullMicrostructureFormException, SQLArgumentException, SQLException {
        surface_deactivations = new ArrayList();
        int[] numbers = Phase.numbers();
        SurfaceDeactivation surfaceDeactivation;
        for (int i = 0; i < numbers.length; i++) {
            int id = numbers[i];
            String name = Phase.name(id);
            if (id!=11 && id != 13 && id != 18) { // skip Inert Filler, Inert Aggregate, and FAC3A
                String htmlCode = Phase.htmlCode(id);
                surfaceDeactivation = new SurfaceDeactivation(id, name, htmlCode, 0.0, 0.0, 1.0, 2.0);
                surface_deactivations.add(surfaceDeactivation);
            }
        }
        
        /**
         * Get microstructure data
         **/
        this.updateMicrostructureData(userName);

        /**
         * Timing
         **/
        this.setDays_hydration_time(Double.toString(Constants.DEFAULT_DAYS_HYDRATION_TIME));
        this.setTerminate_degree("1.0");
        
        /**
         * Simulation parameters
         **/
        this.setParameter_file(Constants.DEFAULT_PARAMETER_FILE);
        this.setTime_conversion_factor(Double.toString(Constants.DEFAULT_TIME_CONVERSION_FACTOR));
        this.setRng_seed("0");
        
        
        
        /**
         *  Curing conditions
         */
        this.setThermal_conditions("isothermal");
        this.setInitial_temperature(Double.toString(Constants.DEFAULT_INITIAL_TEMPERATURE));
        this.setAmbient_temperature(Double.toString(Constants.DEFAULT_AMBIENT_TEMPERATURE));
        this.setHeat_transfer_coefficient(Double.toString(Constants.DEFAULT_HEAT_TRANSFER_COEFFICIENT));
        this.setCement_hydration_activation_energy(Double.toString(Constants.DEFAULT_CEMENT_HYDRATION_ACTIVATION_ENERGY));
        this.setPozzolanic_reactions_activation_energy(Double.toString(Constants.DEFAULT_POZZOLANIC_REACTIONS_ACTIVATION_ENERGY));
        this.setSlag_reactions_activation_energy(Double.toString(Constants.SLAG_DEFAULT_REACTIONS_ACTIVATION_ENERGY));
        this.setSaturation_conditions("saturated");
        this.setCsh_seeds("0.0");
        
        /*
         * Microstructure-related parameters
         */
        // this.setFraction_c3a_orthorhombic("0.0");
        // this.setAggregate_mass_fraction("0.67");
        this.setAggregate_initial_temperature(Double.toString(Constants.DEFAULT_AMBIENT_TEMPERATURE));
        this.setAggregate_heat_transfer_coefficient("0.0");
        this.setCsh_conversion("prohibited");
        this.setCh_precipitation("prohibited");
        
        /*
         * Data Output
         **/
        this.setEvaluate_individual_particle_hydration_times(Double.toString(Constants.DEFAULT_INDIVIDUAL_PARTICLE_HYDRATION_TIMES_EVALUATION_PERIOD));
        this.setEvaluate_percolation_porosity_times(Double.toString(Constants.DEFAULT_PERCOLATION_POROSITY_TIMES_EVALUATION_PERIOD));
        this.setEvaluate_percolation_solids_times(Double.toString(Constants.DEFAULT_PERCOLATION_SOLID_TIMES_EVALUATION_PERIOD));
        this.setPh_influences_hydration_rate(true);
        this.setOutput_option("specify_times");
        this.setOutput_hydrating_microstructure_times(Double.toString(Constants.DEFAULT_OUTPUT_MICROSTRUCTURE_TIMES_PERIOD));
        this.setFile_with_output_times("");
        this.setCreate_movie(false);
         
        
        this.setTemperature_schedule_file("tempdefault.dat");
        /** Reaction Activation Energies **/
                
        
        /**
         *  Hydration Behavior Options
         */
        this.setAdd_crack(false);
        this.setCrack_width("0");
        this.setTime_to_make_crack("10000");
        this.setCrack_parallel_to_axis("yz");
        this.setCreate_movie_frames("0.0");
        //*** Profile management
        // this.setSave_profile(false);
        // String defname = DefaultNameBuilder.buildDefaultName("profile", ".hyd");
        // this.setProfile_name(defname);
        this.setAging_mode(Constants.DEFAULT_AGING_MODE);
        this.setCalorimetry_temperature(Constants.DEFAULT_INITIAL_TEMPERATURE);
        this.setChemical_shrinkage_temperature(Constants.DEFAULT_INITIAL_TEMPERATURE);
    }
    
    /**
     * Holds value of property hydrate_option.
     */
    private String hydrate_option;
    
    /**
     * Holds value of property profile.
     */
    private String profile;
    
    /**
     * Holds value of property microstructure.
     */
    private String microstructure;
    
    /**
     * Holds value of property days_hydration_time.
     */
    private String days_hydration_time;
    
    /**
     * Holds value of property terminate_degree.
     */
    private String terminate_degree;
    
    /**
     * Holds value of property parameter_file.
     */
    private String parameter_file;
    
    /**
     * Holds value of property time_conversion_factor.
     */
    private String time_conversion_factor;
    
    /**
     * Holds value of property thermal_conditions.
     */
    private String thermal_conditions;
    
    /**
     * Holds value of property temperature_schedule_file.
     */
    private String temperature_schedule_file;
    
    /**
     * Holds value of property heat_transfer_coefficient.
     */
    private String heat_transfer_coefficient;
    
    /**
     * Holds value of property initial_temperature.
     */
    private String initial_temperature;
    
    /**
     * Holds value of property ambient_temperature.
     */
    private String ambient_temperature;
    
    /**
     * Holds value of property saturation_conditions.
     */
    private String saturation_conditions;
    
    /**
     * Holds value of property cement_hydration_activation_energy.
     */
    private String cement_hydration_activation_energy;
    
    /**
     * Holds value of property pozzolanic_reactions_activation_energy.
     */
    private String pozzolanic_reactions_activation_energy;
    
    /**
     * Holds value of property slag_reactions_activation_energy.
     */
    private String slag_reactions_activation_energy;

     /**
     * Holds value of property csh_seeds.
     */
    private String csh_seeds;

    /**
     * Holds value of property rng_seed.
     */
    private String rng_seed;
    
    /**
     * Holds value of property fraction_c3a_orthorhombic.
     */
    private String fraction_c3a_orthorhombic;
    
    /**
     * Holds value of property aggregate_mass_fraction.
     */
    private String aggregate_mass_fraction;
    
    /**
     * Holds value of property n1pix.
     */
    private Map n1pix;
    
    /**
     * Holds value of property n1pix.
     */
    private Map bias;
    /**
     * Holds value of property csh_conversion.
     */
    private String csh_conversion;
    
    /**
     * Holds value of property ch_precipitation.
     */
    private String ch_precipitation;
    
    /**
     * Holds value of property slag_characteristics_file.
     */
    private String slag_characteristics_file;
    
    /**
     * Holds value of property has_slag.
     */
    private boolean has_slag;
    
    /**
     * Holds value of property alkali_characteristics_cement_file.
     */
    private String alkali_characteristics_cement_file;
    
    /**
     * Holds value of property has_fly_ash.
     */
    private boolean has_fly_ash;
    
    /**
     * Holds value of property alkali_characteristics_fly_ash_file.
     */
    private String alkali_characteristics_fly_ash_file;
    
    /**
     * Holds value of property pH_influences_hydration_rate.
     */
    private boolean pH_influences_hydration_rate;
    
    /**
     * Holds value of property ph_influences_hydration_rate.
     */
    private boolean ph_influences_hydration_rate;
    
    
    
    
    /**
     * Creates a new instance of HydrateMixForm
     */
    public HydrateMixForm(ActionMapping mapping, HttpServletRequest request) {
        n1pix = new HashMap();
        bias = new HashMap();
        
        reset(mapping, request);
    }
    
    /**
     * Creates a new instance of HydrateMixForm
     */
    public HydrateMixForm() {
    }
    
    /**
     * Getter for property hydrate_option.
     * @return Value of property hydrate_option.
     */
    public String getHydrate_option() {
        
        return this.hydrate_option;
    }
    
    /**
     * Setter for property hydrate_option.
     * @param hydrate_option New value of property hydrate_option.
     */
    public void setHydrate_option(String hydrate_option) {
        
        this.hydrate_option = hydrate_option;
    }
    
    /**
     * Getter for property profile.
     * @return Value of property profile.
     */
    public String getProfile() {
        
        return this.profile;
    }
    
    public void setProfile(String profile) {
        this.profile = profile;
    }
    
    /**
     * Getter for property microstructure.
     * @return Value of property microstructure.
     */
    public String getMicrostructure() {
        
        return this.microstructure;
    }
    
    /**
     * Setter for property microstructure.
     * @param microstructure New value of property microstructure.
     */
    public void setMicrostructure(String microstructure) {
        
        this.microstructure = microstructure;
    }
    
    /**
     * Getter for property days_hydration_time.
     * @return Value of property days_hydration_time.
     */
    public String getDays_hydration_time() {
        
        return this.days_hydration_time;
    }
    
    /**
     * Setter for property days_hydration_time.
     * @param days_hydration_time New value of property days_hydration_time.
     */
    public void setDays_hydration_time(String days_hydration_time) {
        
        this.days_hydration_time = days_hydration_time;
    }
    
    /**
     * Getter for property terminate_degree.
     * @return Value of property terminate_degree.
     */
    public String getTerminate_degree() {
        
        return this.terminate_degree;
    }
    
    /**
     * Setter for property terminate_degree.
     * @param terminate_degree New value of property terminate_degree.
     */
    public void setTerminate_degree(String terminate_degree) {
        
        this.terminate_degree = terminate_degree;
    }
    
    /**
     * Getter for property parameter_file.
     * @return Value of property parameter_file.
     */
    public String getParameter_file() {
        
        return this.parameter_file;
    }
    
    /**
     * Setter for property parameter_file.
     * @param parameter_file New value of property parameter_file.
     */
    public void setParameter_file(String parameter_file) {
        
        this.parameter_file = parameter_file;
    }
    
    /**
     * Getter for property time_conversion_factor.
     * @return Value of property time_conversion_factor.
     */
    public String getTime_conversion_factor() {
        
        return this.time_conversion_factor;
    }
    
    /**
     * Setter for property time_conversion_factor.
     * @param time_conversion_factor New value of property time_conversion_factor.
     */
    public void setTime_conversion_factor(String time_conversion_factor) {
        
        this.time_conversion_factor = time_conversion_factor;
    }
    
    /**
     * Getter for property thermal_conditions.
     * @return Value of property thermal_conditions.
     */
    public String getThermal_conditions() {
        
        return this.thermal_conditions;
    }
    
    /**
     * Setter for property thermal_conditions.
     * @param thermal_conditions New value of property thermal_conditions.
     */
    public void setThermal_conditions(String thermal_conditions) {
        
        this.thermal_conditions = thermal_conditions;
    }
    
    /**
     * Getter for property temperature_schedule_file.
     * @return Value of property temperature_schedule_file.
     */
    public String getTemperature_schedule_file() {
        
        return this.temperature_schedule_file;
    }
    
    /**
     * Setter for property temperature_schedule_file.
     * @param temperature_schedule_file New value of property temperature_schedule_file.
     */
    public void setTemperature_schedule_file(String temperature_schedule_file) {
        
        this.temperature_schedule_file = temperature_schedule_file;
    }
    
    /**
     * Getter for property heat_transfer_coefficient.
     * @return Value of property heat_transfer_coefficient.
     */
    public String getHeat_transfer_coefficient() {
        
        return this.heat_transfer_coefficient;
    }
    
    /**
     * Setter for property heat_transfer_coefficient.
     * @param heat_transfer_coefficient New value of property heat_transfer_coefficient.
     */
    public void setHeat_transfer_coefficient(String heat_transfer_coefficient) {
        
        this.heat_transfer_coefficient = heat_transfer_coefficient;
    }
    
    /**
     * Getter for property initial_temperature.
     * @return Value of property initial_temperature.
     */
    public String getInitial_temperature() {
        
        return this.initial_temperature;
    }
    
    /**
     * Setter for property initial_temperature.
     * @param initial_temperature New value of property initial_temperature.
     */
    public void setInitial_temperature(String initial_temperature) {
        
        this.initial_temperature = initial_temperature;
    }
    
    /**
     * Getter for property ambient_temperature.
     * @return Value of property ambient_temperature.
     */
    public String getAmbient_temperature() {
        
        return this.ambient_temperature;
    }
    
    /**
     * Setter for property ambient_temperature.
     * @param ambient_temperature New value of property ambient_temperature.
     */
    public void setAmbient_temperature(String ambient_temperature) {
        
        this.ambient_temperature = ambient_temperature;
    }
    
    /**
     * Getter for property saturation_conditions.
     * @return Value of property saturation_conditions.
     */
    public String getSaturation_conditions() {
        
        return this.saturation_conditions;
    }
    
    /**
     * Setter for property saturation_conditions.
     * @param saturation_conditions New value of property saturation_conditions.
     */
    public void setSaturation_conditions(String saturation_conditions) {
        
        this.saturation_conditions = saturation_conditions;
    }
    
    /**
     * Getter for property cement_hydration_activation_energy.
     * @return Value of property cement_hydration_activation_energy.
     */
    public String getCement_hydration_activation_energy() {
        
        return this.cement_hydration_activation_energy;
    }
    
    /**
     * Setter for property cement_hydration_activation_energy.
     * @param cement_hydration_activation_energy New value of property cement_hydration_activation_energy.
     */
    public void setCement_hydration_activation_energy(String cement_hydration_activation_energy) {
        
        this.cement_hydration_activation_energy = cement_hydration_activation_energy;
    }
    
    /**
     * Getter for property pozzolanic_reactions_activation_energy.
     * @return Value of property pozzolanic_reactions_activation_energy.
     */
    public String getPozzolanic_reactions_activation_energy() {
        
        return this.pozzolanic_reactions_activation_energy;
    }
    
    /**
     * Setter for property pozzolanic_reactions_activation_energy.
     * @param pozzolanic_reactions_activation_energy New value of property pozzolanic_reactions_activation_energy.
     */
    public void setPozzolanic_reactions_activation_energy(String pozzolanic_reactions_activation_energy) {
        
        this.pozzolanic_reactions_activation_energy = pozzolanic_reactions_activation_energy;
    }
    
    /**
     * Getter for property slag_reactions_activation_energy.
     * @return Value of property slag_reactions_activation_energy.
     */
    public String getSlag_reactions_activation_energy() {
        
        return this.slag_reactions_activation_energy;
    }
    
    /**
     * Setter for property slag_reactions_activation_energy.
     * @param slag_reactions_activation_energy New value of property slag_reactions_activation_energy.
     */
    public void setSlag_reactions_activation_energy(String slag_reactions_activation_energy) {
        
        this.slag_reactions_activation_energy = slag_reactions_activation_energy;
    }

    /**
     * Getter for property csh_seeds
     * @return Value of property csh_seeds.
     */
    public String getCsh_seeds() {

        return this.csh_seeds;
    }

    /**
     * Setter for property csh_seeds.
     * @param csh_seeds New value of property csh_seeds.
     */
    public void setCsh_seeds(String csh_seeds) {

        this.csh_seeds = csh_seeds;
    }

    /**
     * Getter for property rng_seed.
     * @return Value of property rng_seed.
     */
    public String getRng_seed() {
        
        return this.rng_seed;
    }
    
    /**
     * Setter for property rng_seed.
     * @param rng_seed New value of property rng_seed.
     */
    public void setRng_seed(String rng_seed) {
        
        this.rng_seed = rng_seed;
    }
    
    /**
     * Getter for property fraction_c3a_orthorhombic.
     * @return Value of property fraction_c3a_orthorhombic.
     */
    public String getFraction_c3a_orthorhombic() {
        
        return this.fraction_c3a_orthorhombic;
    }
    
    /**
     * Setter for property fraction_c3a_orthorhombic.
     * @param fraction_c3a_orthorhombic New value of property fraction_c3a_orthorhombic.
     */
    public void setFraction_c3a_orthorhombic(String fraction_c3a_orthorhombic) {
        
        this.fraction_c3a_orthorhombic = fraction_c3a_orthorhombic;
    }
    
    /**
     * Getter for property aggregate_mass_fraction.
     * @return Value of property aggregate_mass_fraction.
     */
    public String getAggregate_mass_fraction()  {
        
        return this.aggregate_mass_fraction;
    }
    
    /**
     * Setter for property aggregate_mass_fraction.
     * @param aggregate_volume_fraction New value of property aggregate_mass_fraction.
     */
    public void setAggregate_mass_fraction(String aggregate_mass_fraction)  {
        
        this.aggregate_mass_fraction = aggregate_mass_fraction;
    }
    
    /**
     * Getter for property n1pix.
     * @return Value of property n1pix.
     */
    public Map getN1pix() {
        
        return this.n1pix;
    }
    
    /**
     * Setter for property n1pix.
     * @param n1pix New value of property n1pix.
     */
    public void setN1pix(Map n1pix) {
        this.n1pix = n1pix;
    }
    
    public void setNumOnePixel(String phase, Object number) {
        getN1pix().put(phase, number);
    }
    
    public Object getNumOnePixel(String phase) {
        return getN1pix().get(phase);
    }
    
    public Map getBias() {
        return this.bias;
    }
    
    public void setBias(Map bias) {
        this.bias = bias;
    }
    
    public void setDissolutionBias(String phase, Object value) {
        getBias().put(phase, value);
    }
    
    public Object getDissolutionBias(String phase) {
        return getBias().get(phase);
    }
    
    /**
     * Getter for property csh_conversion.
     * @return Value of property csh_conversion.
     */
    public String getCsh_conversion() {
        
        return this.csh_conversion;
    }
    
    /**
     * Setter for property csh_conversion.
     * @param csh_conversion New value of property csh_conversion.
     */
    public void setCsh_conversion(String csh_conversion) {
        
        this.csh_conversion = csh_conversion;
    }
    
    /**
     * Getter for property ch_precipitation.
     * @return Value of property ch_precipitation.
     */
    public String getCh_precipitation() {
        
        return this.ch_precipitation;
    }
    
    /**
     * Setter for property ch_precipitation.
     * @param ch_precipitation New value of property ch_precipitation.
     */
    public void setCh_precipitation(String ch_precipitation) {
        
        this.ch_precipitation = ch_precipitation;
    }
    
    /**
     * Getter for property slag_characteristics_file.
     * @return Value of property slag_characteristics_file.
     */
    public String getSlag_characteristics_file() {
        
        return this.slag_characteristics_file;
    }
    
    public void setSlag_characteristics_file(String file) {
        this.slag_characteristics_file = file;
    }
    
    /**
     * Getter for property has_slag.
     * @return Value of property has_slag.
     */
    public boolean isHas_slag() {
        
        return this.has_slag;
    }
    
    /**
     * Setter for property has_slag.
     * @param has_slag New value of property has_slag.
     */
    public void setHas_slag(boolean has_slag) {
        
        this.has_slag = has_slag;
    }
    
    /**
     * Getter for property alkali_characteristics_cement_file.
     * @return Value of property alkali_characteristics_cement_file.
     */
    public String getAlkali_characteristics_cement_file() {
        
        return this.alkali_characteristics_cement_file;
    }
    
    /**
     * Setter for property alkali_characteristics_cement_file.
     * @param alkali_characteristics_cement_file New value of property alkali_characteristics_cement_file.
     */
    public void setAlkali_characteristics_cement_file(String alkali_characteristics_cement_file) {
        
        this.alkali_characteristics_cement_file = alkali_characteristics_cement_file;
    }
    
    /**
     * Getter for property has_fly_ash.
     * @return Value of property has_fly_ash.
     */
    public boolean isHas_fly_ash() {
        
        return this.has_fly_ash;
    }
    
    /**
     * Setter for property has_fly_ash.
     * @param has_fly_ash New value of property has_fly_ash.
     */
    public void setHas_fly_ash(boolean has_fly_ash) {
        
        this.has_fly_ash = has_fly_ash;
    }
    
    /**
     * Getter for property alkali_characteristics_fly_ash_file.
     * @return Value of property alkali_characteristics_fly_ash_file.
     */
    public String getAlkali_characteristics_fly_ash_file() {
        
        return this.alkali_characteristics_fly_ash_file;
    }
    
    /**
     * Setter for property alkali_characteristics_fly_ash_file.
     * @param alkali_characteristics_fly_ash_file New value of property alkali_characteristics_fly_ash_file.
     */
    public void setAlkali_characteristics_fly_ash_file(String alkali_characteristics_fly_ash_file) {
        
        this.alkali_characteristics_fly_ash_file = alkali_characteristics_fly_ash_file;
    }
    
    /**
     * Getter for property ph_influences_hydration_rate.
     * @return Value of property ph_influences_hydration_rate.
     */
    public boolean isPh_influences_hydration_rate() {
        
        return this.ph_influences_hydration_rate;
    }
    
    /**
     * Setter for property ph_influences_hydration_rate.
     * @param ph_influences_hydration_rate New value of property ph_influences_hydration_rate.
     */
    public void setPh_influences_hydration_rate(boolean ph_influences_hydration_rate) {
        
        this.ph_influences_hydration_rate = ph_influences_hydration_rate;
    }
    
    /**
     * Holds value of property add_crack.
     */
    private boolean add_crack;
    
    /**
     * Getter for property add_crack.
     * @return Value of property add_crack.
     */
    public boolean isAdd_crack() {
        
        return this.add_crack;
    }
    
    /**
     * Setter for property add_crack.
     * @param add_crack New value of property add_crack.
     */
    public void setAdd_crack(boolean add_crack) {
        
        this.add_crack = add_crack;
    }
    
    /**
     * Holds value of property crack_width.
     */
    private String crack_width;
    
    /**
     * Getter for property crack_width.
     * @return Value of property crack_width.
     */
    public String getCrack_width() {
        
        return this.crack_width;
    }
    
    /**
     * Setter for property crack_width.
     * @param crack_width New value of property crack_width.
     */
    public void setCrack_width(String crack_width) {
        
        this.crack_width = crack_width;
    }
    
    /**
     * Holds value of property time_to_make_crack.
     */
    private String time_to_make_crack;
    
    /**
     * Getter for property time_to_make_crack.
     * @return Value of property time_to_make_crack.
     */
    public String getTime_to_make_crack() {
        
        return this.time_to_make_crack;
    }
    
    /**
     * Setter for property time_to_make_crack.
     * @param time_to_make_crack New value of property time_to_make_crack.
     */
    public void setTime_to_make_crack(String time_to_make_crack) {
        
        this.time_to_make_crack = time_to_make_crack;
    }
    
    /**
     * Holds value of property crack_parallel_to_axis.
     */
    private String crack_parallel_to_axis;
    
    /**
     * Getter for property crack_parallel_to_axis.
     * @return Value of property crack_parallel_to_axis.
     */
    public String getCrack_parallel_to_axis() {
        
        return this.crack_parallel_to_axis;
    }
    
    /**
     * Setter for property crack_parallel_to_axis.
     * @param crack_parallel_to_axis New value of property crack_parallel_to_axis.
     */
    public void setCrack_parallel_to_axis(String crack_parallel_to_axis) {
        
        this.crack_parallel_to_axis = crack_parallel_to_axis;
    }
    
    /**
     * Holds value of property evaluate_percolation_porosity_times.
     */
    private String evaluate_percolation_porosity_times;
    
    /**
     * Getter for property evaluate_percolation_cycles.
     * @return Value of property evaluate_percolation_cycles.
     */
    public String getEvaluate_percolation_porosity_times()  {
        
        return this.evaluate_percolation_porosity_times;
    }
    
    /**
     * Setter for property evaluate_percolation_cycles.
     * @param evaluate_percolation_cycles New value of property evaluate_percolation_cycles.
     */
    public void setEvaluate_percolation_porosity_times(String evaluate_percolation_porosity_times)  {
        
        this.evaluate_percolation_porosity_times = evaluate_percolation_porosity_times;
    }
    
    /**
     * Holds value of property evaluate_percolation_solids_times.
     */
    private String evaluate_percolation_solids_times;
    
    /**
     * Getter for property evaluate_percolation_solids_times.
     * @return Value of property evaluate_percolation_solids_times.
     */
    public String getEvaluate_percolation_solids_times() {
        
        return this.evaluate_percolation_solids_times;
    }
    
    /**
     * Setter for property evaluate_percolation_solids_times.
     * @param evaluate_percolation_solids_times New value of property evaluate_percolation_solids_times.
     */
    public void setEvaluate_percolation_solids_times(String evaluate_percolation_solids_times) {
        
        this.evaluate_percolation_solids_times = evaluate_percolation_solids_times;
    }
    
    /**
     * Holds value of property evaluate_individual_particle_hydration_times.
     */
    private String evaluate_individual_particle_hydration_times;
    
    /**
     * Getter for property evaluate_individual_particle_hydration_times.
     * @return Value of property evaluate_individual_particle_hydration_times.
     */
    public String getEvaluate_individual_particle_hydration_times() {
        
        return this.evaluate_individual_particle_hydration_times;
    }
    
    /**
     * Setter for property evaluate_individual_particle_hydration_times.
     * @param evaluate_individual_particle_hydration_times New value of property evaluate_individual_particle_hydration_times.
     */
    public void setEvaluate_individual_particle_hydration_times(String evaluate_individual_particle_hydration_times) {
        
        this.evaluate_individual_particle_hydration_times = evaluate_individual_particle_hydration_times;
    }
    
    /**
     * Holds value of property output_hydrating_microstructure_times.
     */
    private String output_hydrating_microstructure_times;
    
    /**
     * Getter for property output_hydrating_microstructure_times.
     * @return Value of property output_hydrating_microstructure_times.
     */
    public String getOutput_hydrating_microstructure_times() {
        
        return this.output_hydrating_microstructure_times;
    }
    
    /**
     * Setter for property output_hydrating_microstructure_times.
     * @param output_hydrating_microstructure_times New value of property output_hydrating_microstructure_times.
     */
    public void setOutput_hydrating_microstructure_times(String output_hydrating_microstructure_times) {
        
        this.output_hydrating_microstructure_times = output_hydrating_microstructure_times;
    }
    
    /**
     * Holds value of property file_with_output_times.
     */
    private String file_with_output_times;
    
    /**
     * Getter for property file_with_output_times.
     * @return Value of property file_with_output_times.
     */
    public String getFile_with_output_times() {
        
        return this.file_with_output_times;
    }
    
    /**
     * Setter for property file_with_output_times.
     * @param file_with_output_times New value of property file_with_output_times.
     */
    public void setFile_with_output_times(String file_with_output_times) {
        
        this.file_with_output_times = file_with_output_times;
    }
    
    /**
     * Holds value of property create_movie_frames.
     */
    private String create_movie_frames;
    
    /**
     * Getter for property create_movie_frames.
     * @return Value of property create_movie_frames.
     */
    public String getCreate_movie_frames() {
        
        return this.create_movie_frames;
    }
    
    /**
     * Setter for property create_movie_frames.
     * @param create_movie_frames New value of property create_movie_frames.
     */
    public void setCreate_movie_frames(String create_movie_frames) {
        
        this.create_movie_frames = create_movie_frames;
    }
    
    /**
     * Getter for property disrealnew_input.
     * @return Value of property disrealnew_input.
     */
    public String getDisrealnew_input(String userName) throws DBFileException, SQLArgumentException, SQLException {
        return generateInputForUser(userName);
    }
    
    private String generateInputForUser(String userName) throws DBFileException, SQLArgumentException, SQLException {
        StringBuffer input = new StringBuffer();
        // String parametersFilesDir = Vcctl.getParametersFilesDirectory();
        
        String destination = ServerFile.getUserOperationDir(userName, getOperation_name()) + Constants.PARAMETER_FILE;
        ServerFile.writeTextFile(destination,CementDatabase.getParameterFileData(getParameter_file()));

        // First, output path to parameters file
        input.append(destination).append("\n");
        
        // RNG seed
        int rng_seed = Integer.valueOf(getRng_seed());
        if (rng_seed == 0 || isUse_own_random_seed() == false) {
            // get an integer between -32768 and 0
            rng_seed = -(int)(Math.round(Math.random()*Math.pow(2.0,15.0)));
        }
        this.setRng_seed(Integer.toString(rng_seed));
        input.append(getRng_seed()).append("\n");
        
        // Microstructure files
        String microname = getMicrostructure();
        
        String microImgFile = microname;
        String pmicroImgFile = microname;
        
        if (microImgFile.indexOf(".img") < 0) {
            microImgFile += ".img";
        }
        if (pmicroImgFile.indexOf(".pimg") < 0) {
            pmicroImgFile += ".pimg";
        }
        
        String microdir = ServerFile.getUserOperationDir(userName, microname);
        if (!microdir.endsWith(File.separator)) {
            microdir = microdir + File.separator;
        }
        
        // First, output microstructure directory, then img file
        // and pimg file names.
        input.append(microdir).append("\n");
        input.append(microImgFile).append("\n");
        input.append(pmicroImgFile).append("\n");
        
        // Directory to which output files should be written
        String opdir = ServerFile.getUserOperationDir(userName, getOperation_name());
        if (!opdir.endsWith(File.separator)) {
            opdir = opdir + File.separator;
        }
        
        input.append(opdir).append("\n");
        
        // Fraction of C3A that is orthorhombic
        input.append(getFraction_c3a_orthorhombic()).append("\n");

        // Number of CSH seeds per mL of water in the mix
        input.append(getCsh_seeds()).append("\n");
        
        // Enter number of days of the hydration
        input.append(getDays_hydration_time()).append("\n");
        
        // Add a crack (y/n)?
        if (isAdd_crack()) {
            input.append('y').append("\n");
            input.append(getCrack_width()).append("\n");
            input.append(getTime_to_make_crack()).append("\n");
            String axis = getCrack_parallel_to_axis();
            int naxis;
            if (axis.equalsIgnoreCase("xz")) { naxis = 2; } else if (axis.equalsIgnoreCase("xy")) { naxis = 3; } else { naxis = 1; }
            input.append(naxis).append("\n");
        } else {
            input.append('n').append("\n");
        }
        
        // Customize output microstructure at different degrees of hydration (y/n)?
        if (getOutput_option().equalsIgnoreCase("specify_file")) {
            input.append('y').append("\n");
            
            // Write file with output times
            destination = ServerFile.getUserOperationDir(userName, getOperation_name()) + Constants.TIMING_OUTPUT_FILE;
            ServerFile.writeTextFile(destination,CementDatabase.getTimingOutputFileData(getFile_with_output_times()));
            // input.append(destination).append("\n");
        } else {
            input.append('n').append("\n");
            input.append(getOutput_hydrating_microstructure_times()).append("\n");
        }
        
        // Enter bias numbers for each phase present
        // Read in bias file and append as-is
        String bias_input = ServerFile.readUserOpTextFile(userName, microname, microname+".bias");
        input.append(bias_input);
        
                // Initial temperature of binder in degrees Celsius
        input.append(getInitial_temperature()).append("\n");
        
        int hydration_conditions;
        String hc = getThermal_conditions();
        if (hc.equalsIgnoreCase("isothermal")) {
            this.setAmbient_temperature(this.getInitial_temperature());
            this.setHeat_transfer_coefficient(Double.toString(Constants.DEFAULT_HEAT_TRANSFER_COEFFICIENT));
            hydration_conditions = 0;
        } else if (hc.equalsIgnoreCase("use schedule")) {
            hydration_conditions = 2;
        } else if (!(hc.equalsIgnoreCase("semi-adiabatic"))) {
            this.setAmbient_temperature(this.getInitial_temperature());
            this.setHeat_transfer_coefficient(Double.toString(Constants.DEFAULT_HEAT_TRANSFER_COEFFICIENT));
            hydration_conditions = 1;
        } else {
            hydration_conditions = 1;
        }
        // Hydration conditions 0: isothermal, 1: adiabatic, 2: programmed conditions
        //
        // If (2) is chosen, user will be prompted for file with conditions at
        // the end
        input.append(hydration_conditions).append("\n");
        // Ambient temperature in degrees Celsius
        input.append(getAmbient_temperature()).append("\n");
        // Overall heat transfer coefficient J/g/C/s
        input.append(getHeat_transfer_coefficient()).append("\n");
        // Apparent activation energy for hydration kJ/mole
        input.append(getCement_hydration_activation_energy()).append("\n");
        // Apparent activation energy for pozzolanic reactions in kJ/mole
        input.append(getPozzolanic_reactions_activation_energy()).append("\n");
        // Apparent activation energy for slag reactions in kJ/mole
        input.append(getSlag_reactions_activation_energy()).append("\n");
        
        // Type of time calibration to use.
        if (this.aging_mode.equalsIgnoreCase("calorimetry")) {
            // Isothermal calorimetry
            input.append("1").append("\n");
            destination = ServerFile.getUserOperationDir(userName, getOperation_name()) + Constants.CALORIMETRY_FILE;
            ServerFile.writeTextFile(destination,CementDatabase.getCalorimetryFileData(this.getCalorimetry_file()));
            
            // Write calorimetry full path
            input.append(Constants.CALORIMETRY_FILE).append("\n");
            
            // Write temperature of calorimetry file
            input.append(this.getCalorimetry_temperature()).append("\n");
        } else if (this.aging_mode.equalsIgnoreCase("chemical_shrinkage")) {
            // Chemical Shrinkage
            input.append("2").append("\n");
            
            // Create chemical shrinkage data file
            destination = ServerFile.getUserOperationDir(userName, getOperation_name()) + Constants.CHEMICAL_SHRINKAGE_FILE;
            ServerFile.writeTextFile(destination,CementDatabase.getChemicalShrinkageFileData(this.getChemical_shrinkage_file()));
            // Write chemical shrinkage data file full path
            input.append(Constants.CHEMICAL_SHRINKAGE_FILE).append("\n");
            
            // Write temperature of chemical shrinkage data file
            input.append(this.getChemical_shrinkage_temperature()).append("\n");
        } else {
            // aging_mode should be "time" here
            // Time
            input.append("0").append("\n");
            
            // Kinetic factor to convert cycles to time
            input.append(getTime_conversion_factor()).append("\n");
        }
        
        
        
        // Degree of hydration at which to terminate
        input.append(getTerminate_degree()).append("\n");
        
        // Hydration under saturation or sealed?
        int saturation_condition;
        if (getSaturation_conditions().equalsIgnoreCase("saturated")) {
            saturation_condition = 0;
        } else {
            saturation_condition = 1;
        }
        input.append(saturation_condition).append("\n");
        
        // Cycle frequency for checking pore space (porosity) percolation
        input.append(getEvaluate_percolation_porosity_times()).append("\n");
        
        // Cycle frequency for checking solids percolation
        input.append(getEvaluate_percolation_solids_times()).append("\n");
        
        // Cycle frequency for checking individual particle percolation
        input.append(getEvaluate_individual_particle_hydration_times()).append("\n");
        

        // Aggregate mass fraction
        input.append(getAggregate_mass_fraction()).append("\n");
        // Initial temperature of aggregate in concrete
        input.append(getAggregate_initial_temperature()).append("\n");
        // Heat transfer coefficient between aggregate and binder
        input.append(getAggregate_heat_transfer_coefficient()).append("\n");
        
        // Conversion of C-S-H to pozzolanic C-S-H allowed?
        int conversion_allowed;
        if (getCsh_conversion().equalsIgnoreCase("prohibited")) {
            conversion_allowed = 0;
        } else {
            conversion_allowed = 1;
        }
        input.append(conversion_allowed).append("\n");
        // C-H precipitation allowed?
        int ch_precipitation_allowed;
        if (getCh_precipitation().equalsIgnoreCase("prohibited")) {
            ch_precipitation_allowed = 0;
        } else {
            ch_precipitation_allowed = 1;
        }
        input.append(ch_precipitation_allowed).append("\n");
        // Number of frames in hydration movie
        input.append(getCreate_movie_frames()).append("\n");
        // For all phases:
        // Phase id of surface to deactivate
        // Fraction of surface to deactivate
        // Time to implement
        // Time to begin
        // Time of full reactivation
        
        // -1 for end of surface deactivation
        SurfaceDeactivation surfaceDeactivation;
        Double surfaceFractionToDeactivate;
        for (int i = 0; i < surface_deactivations.size(); i++) {
            surfaceDeactivation = (SurfaceDeactivation)surface_deactivations.get(i);
            surfaceFractionToDeactivate = surfaceDeactivation.getSurface_fraction_to_deactivate();
            if (surfaceFractionToDeactivate > 0.0) {
                input.append(Integer.toString(surfaceDeactivation.getPhase_id())).append("\n");
                input.append(Double.toString(surfaceFractionToDeactivate)).append("\n");
                input.append(Double.toString(surfaceDeactivation.getDeactivation_time())).append("\n");
                input.append(Double.toString(surfaceDeactivation.getReactivation_begin_time())).append("\n");
                input.append(Double.toString(surfaceDeactivation.getFull_reactivation_time())).append("\n");
            }
        }
        input.append(-1).append("\n");
        
        // pH influence kinetics (yes/no)
        if (isPh_influences_hydration_rate()) {
            input.append(1);
        } else {
            input.append(0);
        }
        input.append("\n");
        
        // Input key (value not used)
        input.append(1).append("\n");
        
        /*
        String dir = Vcctl.getPublicDir();
        // Alkali characteristics file for cement
        input.append(dir+getAlkali_characteristics_cement_file()).append("\n");
        */
        /**
         * Always write out an alkali characteristics for fly ash file
         */
        /*
        // Flyash file, if present
        if (isHas_fly_ash()) {
            input.append(dir+getAlkali_characteristics_fly_ash_file()).append("\n");
        } else {
            // Write out file with four 0.0s
            input.append(dir+"noflyash.dat").append("\n");
        }
        
        // Slag characteristics file, if present
        String opdir = ServerFile.getOperationDir(getOperation_name());
        if (isHas_slag()) {
            // The slag characteristics file goes in the operation directory
            input.append(opdir+"/"+getSlag_characteristics_file()).append("\n");
        }
        
        // Fully resolved name of temperature history file, if needed
        if (hydration_conditions == 2) {
            input.append(dir+getTemperature_schedule_file()).append("\n");
        }
         **/
        
        return input.toString();
    }
    
    /**
     * Holds value of property output_option.
     */
    private String output_option;
    
    /**
     * Getter for property output_option.
     * @return Value of property output_option.
     */
    public String getOutput_option() {
        
        return this.output_option;
    }
    
    /**
     * Setter for property output_option.
     * @param output_option New value of property output_option.
     */
    public void setOutput_option(String output_option) {
        
        this.output_option = output_option;
    }
    
    /**
     * Holds value of property aggregate_initial_temperature.
     */
    private String aggregate_initial_temperature;
    
    /**
     * Getter for property aggregate_initial_temperature.
     * @return Value of property aggregate_initial_temperature.
     */
    public String getAggregate_initial_temperature() {
        
        return this.aggregate_initial_temperature;
    }
    
    /**
     * Setter for property aggregate_initial_temperature.
     * @param aggregate_initial_temperature New value of property aggregate_initial_temperature.
     */
    public void setAggregate_initial_temperature(String aggregate_initial_temperature) {
        
        this.aggregate_initial_temperature = aggregate_initial_temperature;
    }
    
    /**
     * Holds value of property aggregate_heat_transfer_coefficient.
     */
    private String aggregate_heat_transfer_coefficient;
    
    /**
     * Getter for property aggregate_heat_transfer_coefficient.
     * @return Value of property aggregate_heat_transfer_coefficient.
     */
    public String getAggregate_heat_transfer_coefficient() {
        
        return this.aggregate_heat_transfer_coefficient;
    }
    
    /**
     * Setter for property aggregate_heat_transfer_coefficient.
     * @param aggregate_heat_transfer_coefficient New value of property aggregate_heat_transfer_coefficient.
     */
    public void setAggregate_heat_transfer_coefficient(String aggregate_heat_transfer_coefficient) {
        
        this.aggregate_heat_transfer_coefficient = aggregate_heat_transfer_coefficient;
    }
    
    /**
     * Holds value of property save_profile.
     */
    private boolean save_profile;
    
    /**
     * Getter for property save_profile.
     * @return Value of property save_profile.
     */
    public boolean isSave_profile() {
        
        return this.save_profile;
    }
    
    /**
     * Setter for property save_profile.
     * @param save_profile New value of property save_profile.
     */
    public void setSave_profile(boolean save_profile) {
        
        this.save_profile = save_profile;
    }
    
    /**
     * Holds value of property profile_name.
     */
    private String profile_name;
    
    /**
     * Getter for property profile_name.
     * @return Value of property profile_name.
     */
    public String getProfile_name() {
        
        return this.profile_name;
    }
    
    /**
     * Setter for property profile_name.
     * @param profile_name New value of property profile_name.
     */
    public void setProfile_name(String profile_name) {
        
        this.profile_name = profile_name;
    }
    
    /**
     * copy properties from hmfi into hmf
     */
    /*
    public static void copy(HydrateMixForm hmf, HydrateMixForm hmfi) {
        //****
        hmf.setNumber_hydration_cycles(hmfi.getNumber_hydration_cycles());
        hmf.setTerminate_degree(hmfi.getTerminate_degree());
        hmf.setParameter_file(hmfi.getParameter_file());
        hmf.setTime_conversion_factor(hmfi.getTime_conversion_factor());
        hmf.setThermal_conditions(hmfi.getThermal_conditions());
        hmf.setTemperature_schedule_file(hmfi.getTemperature_schedule_file());
        hmf.setHeat_transfer_coefficient(hmfi.getHeat_transfer_coefficient());
        hmf.setInitial_temperature(hmfi.getInitial_temperature());
        hmf.setAmbient_temperature(hmfi.getAmbient_temperature());
        hmf.setSaturation_conditions(hmfi.getSaturation_conditions());
        hmf.setCement_hydration_activation_energy(hmfi.getCement_hydration_activation_energy());
        hmf.setPozzolanic_reactions_activation_energy(hmfi.getPozzolanic_reactions_activation_energy());
        hmf.setSlag_reactions_activation_energy(hmfi.getSlag_reactions_activation_energy());
        //****
        hmf.setRng_seed(hmfi.getRng_seed());
        hmf.setFraction_c3a_orthorhombic(hmfi.getFraction_c3a_orthorhombic());
        hmf.setAggregate_mass_fraction(hmfi.getAggregate_mass_fraction());
        hmf.setAggregate_initial_temperature(hmfi.getAggregate_initial_temperature());
        hmf.setAggregate_heat_transfer_coefficient(hmfi.getAggregate_heat_transfer_coefficient());
        
        hmf.setCsh_conversion(hmfi.getCsh_conversion());
        hmf.setCh_precipitation(hmfi.getCh_precipitation());
        hmf.setSlag_characteristics_file(hmfi.getSlag_characteristics_file());
        hmf.setAlkali_characteristics_cement_file(hmfi.getAlkali_characteristics_cement_file());
        hmf.setAlkali_characteristics_fly_ash_file(hmfi.getAlkali_characteristics_fly_ash_file());
        hmf.setPh_influences_hydration_rate(hmfi.isPh_influences_hydration_rate());
        hmf.setHas_slag(hmfi.isHas_slag());
        hmf.setHas_fly_ash(hmfi.isHas_fly_ash());
        hmf.setAdd_crack(hmfi.isAdd_crack());
        hmf.setCrack_width(hmfi.getCrack_width());
        hmf.setCycle_to_make_crack(hmfi.getCycle_to_make_crack());
        hmf.setCrack_parallel_to_axis(hmfi.getCrack_parallel_to_axis());
        hmf.setEvaluate_individual_particle_hydration_cycles(hmfi.getEvaluate_individual_particle_hydration_cycles());
        hmf.setEvaluate_percolation_porosity_cycles(hmfi.getEvaluate_percolation_porosity_cycles());
        hmf.setEvaluate_percolation_solids_cycles(hmfi.getEvaluate_percolation_solids_cycles());
        hmf.setOutput_option(hmfi.getOutput_option());
        hmf.setOutput_hydrating_microstructure_cycles(hmfi.getOutput_hydrating_microstructure_cycles());
        hmf.setFile_with_output_cycles(hmfi.getFile_with_output_cycles());
        hmf.setCreate_movie_frames(hmfi.getCreate_movie_frames());
        hmf.setSave_profile(hmfi.isSave_profile());
        hmf.setProfile_name(hmfi.getProfile_name());
        hmf.setOperation_name(hmfi.getOperation_name());
        //***
    }
     **/
    
    /**
     * Holds value of property operation_name.
     */
    private String operation_name;
    
    /**
     * Getter for property operation_name.
     * @return Value of property operation_name.
     */
    public String getOperation_name() {
        
        return this.operation_name;
    }
    
    /**
     * Setter for property operation_name.
     * @param operation_name New value of property operation_name.
     */
    public void setOperation_name(String operation_name) {
        
        this.operation_name = operation_name;
    }
    
    /**
     * Holds value of property notes.
     */
    private String notes;
    
    /**
     * Getter for property notes.
     * @return Value of property notes.
     */
    public String getNotes() {
        return this.notes;
    }
    
    /**
     * Setter for property notes.
     * @param notes New value of property notes.
     */
    public void setNotes(String notes) {
        this.notes = notes;
    }
    
    /**
     * Holds value of property use_own_random_seed.
     */
    private boolean use_own_random_seed;
    
    /**
     * Getter for property use_own_random_seed.
     * @return Value of property use_own_random_seed.
     */
    public boolean isUse_own_random_seed() {
        return this.use_own_random_seed;
    }
    
    /**
     * Setter for property use_own_random_seed.
     * @param use_own_random_seed New value of property use_own_random_seed.
     */
    public void setUse_own_random_seed(boolean use_own_random_seed) {
        this.use_own_random_seed = use_own_random_seed;
    }
    
    /**
     * Holds value of property user_mix_list.
     */
    private Collection user_mix_list;
    
    /**
     * Getter for property user_mix_list.
     * @return Value of property user_mix_list.
     */
    public Collection getUser_mix_list() {
        return this.user_mix_list;
    }
    
    /**
     * Setter for property user_mix_list.
     * @param user_mix_list New value of property user_mix_list.
     */
    public void setUser_mix_list(Collection user_mix_list) {
        this.user_mix_list = user_mix_list;
    }

    /**
     * Holds value of property has_aggregate.
     */
    private boolean has_aggregate;

    /**
     * Getter for property has_aggregate.
     * @return Value of property has_aggregate.
     */
    public boolean isHas_aggregate() {
        return this.has_aggregate;
    }

    /**
     * Setter for property has_aggregate.
     * @param has_aggregate New value of property has_aggregate.
     */
    public void setHas_aggregate(boolean has_aggregate) {
        this.has_aggregate = has_aggregate;
    }

    /**
     * Holds value of property has_silica_fume.
     */
    private boolean has_silica_fume;

    /**
     * Getter for property has_silica_fume.
     * @return Value of property has_silica_fume.
     */
    public boolean isHas_silica_fume() {
        return this.has_silica_fume;
    }

    /**
     * Setter for property has_silica_fume.
     * @param has_silica_fume New value of property has_silica_fume.
     */
    public void setHas_silica_fume(boolean has_silica_fume) {
        this.has_silica_fume = has_silica_fume;
    }

    public void updateMicrostructureData(String userName)
        throws NullMicrostructureException, NullMicrostructureFormException, SQLArgumentException, SQLException {
        
        /**
         * Get information from the microstructure
         */
        
        if (microstructure != null) {
            GenerateMicrostructureForm microstructureForm = GenerateMicrostructureForm.create_from_state(microstructure,userName);
            
            if (microstructureForm != null) {
                String defopname = "";
                
                if (microstructure == null || microstructure.equalsIgnoreCase("")) {
                    defopname = DefaultNameBuilder.buildDefaultOperationNameForUser("MyHydration", "", userName);
                } else {
                    defopname = DefaultNameBuilder.buildDefaultOperationNameForUser("HydrationOf-" + microstructure, "", userName);
                    defopname = defopname.replace(".img","");
                }
                this.setOperation_name(defopname);
                
                String ms = OperationDatabase.getOperationStatusForUser(microstructure,userName);
                this.setMixingStatus(ms);
                this.setAlkali_characteristics_cement_file(CementDatabase.getCementAlkaliFile(microstructureForm.getCementName()));
                
                /**
                 * Get the fraction of C3A that is orthorombic
                 */
                this.setFraction_c3a_orthorhombic(microstructureForm.getFraction_orthorombic_c3a());
                
                /**
                 * Determine if slag is present, and if so, what is the name of the
                 * slag characteristics file
                 */
                boolean has_slag = false;
                double massFrac = Double.parseDouble(microstructureForm.getSlag_massfrac());
                if (massFrac > 0.0) {
                    has_slag = true;
                } else {
                    String slag_sample = microstructureForm.getSlag_sample();
                    if (!slag_sample.equalsIgnoreCase("not present") &&
                            !slag_sample.equalsIgnoreCase("none") &&
                            (slag_sample.length() > 0)) {
                        has_slag = true;
                    }
                }
                String slagCharacteristicsFile = null;
                if (has_slag) {
                    // slagCharacteristicsFile = CementDatabase.getFlyAshAlkaliFile(microstructureForm.getSlag_psd());
                    slagCharacteristicsFile = CementDatabase.getSlagCharacteristicsFile(microstructureForm.getSlag_psd());
                    if (slagCharacteristicsFile == null || slagCharacteristicsFile.equalsIgnoreCase(""))
                        slagCharacteristicsFile = Constants.DEFAULT_SLAG_CHARACTERISTICS_FILE;
                } else {
                    slagCharacteristicsFile = Constants.NO_SLAG_CHARACTERISTICS_FILE;
                }
                this.setSlag_characteristics_file(slagCharacteristicsFile);
                this.setHas_slag(has_slag);
                
                /**
                 * Determine if fly ash is present, and if so, what is the name of
                 * the fly ash
                 */
                boolean has_fly_ash = false;
                massFrac = Double.parseDouble(microstructureForm.getFly_ash_massfrac());
                if (massFrac > 0.0) {
                    has_fly_ash = true;
                } else {
                    String fa_sample = microstructureForm.getFly_ash_sample();
                    if (!fa_sample.equalsIgnoreCase("not present") &&
                            !fa_sample.equalsIgnoreCase("none") &&
                            (fa_sample.length() > 0)) {
                        has_fly_ash = true;
                    }
                }
                String flyAshAlkaliCharacteristicsFile = null;
                if (has_fly_ash) {
                    // flyAshAlkaliCharacteristicsFile = CementDatabase.getSlagCharacteristicsFile(microstructureForm.getFly_ash_psd());
                    flyAshAlkaliCharacteristicsFile = CementDatabase.getFlyAshAlkaliFile(microstructureForm.getFly_ash_psd());
                    if (flyAshAlkaliCharacteristicsFile == null || flyAshAlkaliCharacteristicsFile.equalsIgnoreCase(""))
                        flyAshAlkaliCharacteristicsFile = Constants.DEFAULT_FLY_ASH_ALKALI_CHARACTERISTICS_FILE;
                } else {
                    flyAshAlkaliCharacteristicsFile = Constants.NO_FLY_ASH_ALKALI_CHARACTERISTICS_FILE;
                }
                this.setAlkali_characteristics_fly_ash_file(flyAshAlkaliCharacteristicsFile);
                this.setHas_fly_ash(has_fly_ash);
                
                
                /**
                 * Determine if aggregate is present
                 */
                
                boolean has_aggregate = false;
                massFrac = Double.parseDouble(microstructureForm.getCoarse_aggregate01_massfrac());
                massFrac += Double.parseDouble(microstructureForm.getCoarse_aggregate02_massfrac());
                massFrac += Double.parseDouble(microstructureForm.getFine_aggregate01_massfrac());
                massFrac += Double.parseDouble(microstructureForm.getFine_aggregate02_massfrac());
                
                if (microstructureForm.isAdd_aggregate() && massFrac > 0) {
                    has_aggregate = true;
                }
                
                this.setHas_aggregate(has_aggregate);
                this.setAggregate_mass_fraction(Double.toString(massFrac));
                
                
                /**
                 * Determine if silica fume is present
                 */
                
                boolean has_silica_fume = false;
                massFrac = Double.parseDouble(microstructureForm.getSilica_fume_massfrac());
                if (massFrac > 0) {
                    has_silica_fume = true;
                }
                
                this.setHas_silica_fume(has_silica_fume);
                
                /**********************************************************************
                 * Get the state information for the microstructure selected and use it
                 * to determine characteristic files for
                 * (1) alkali for cement
                 * (2) alkali for fly ash
                 * (3) slag characteristics file
                 *********************************************************************/
                
                // Determine alkali file for cement
                /*
                String cement_name = microstructureForm.getCement_psd();
                this.setAlkali_characteristics_cement_file(CementDatabase.getCementAlkaliFile(cement_name));
                
                // Determine alkali file for fly ash
                String fly_ash_name = microstructureForm.getFly_ash_psd();
                this.setAlkali_characteristics_fly_ash_file(CementDatabase.getFlyAshAlkaliFile(fly_ash_name));
                
                // Determine alkali file for fly ash
                String slag_name = microstructureForm.getSlag_psd();
                this.setSlag_characteristics_file(CementDatabase.getSlagCharacteristicsFile(slag_name));
                 **/
            } else {
                throw new NullMicrostructureFormException("No microstructure form");
            }
        } else {
            throw new NullMicrostructureException("No microstructure");
        }
    }

    /**
     * Getter for property has_slag_or_fly_ash_or_silica_fume.
     * @return Value of property has_slag_or_fly_ash_or_silica_fume.
     */
    public boolean isHas_slag_or_fly_ash_or_silica_fume() {
        return (this.has_fly_ash || this.has_silica_fume || this.has_slag);
    }

    /**
     * Holds value of property create_movie.
     */
    private boolean create_movie;

    /**
     * Getter for property create_movie.
     * @return Value of property create_movie.
     */
    public boolean isCreate_movie() {
        return this.create_movie;
    }

    /**
     * Setter for property create_movie.
     * @param create_movie New value of property create_movie.
     */
    public void setCreate_movie(boolean create_movie) {
        this.create_movie = create_movie;
    }

    /**
     * Holds value of property mixingStatus.
     */
    private String mixingStatus;

    /**
     * Getter for property mixingStatus.
     * @return Value of property mixingStatus.
     */
    public String getMixingStatus() {
        return this.mixingStatus;
    }

    /**
     * Setter for property mixingStatus.
     * @param mixingStatus New value of property mixingStatus.
     */
    public void setMixingStatus(String mixingStatus) {
        this.mixingStatus = mixingStatus;
    }

    /**
     * Holds value of property surface_deactivations.
     */
    private ArrayList surface_deactivations;

    /**
     * Getter for property surface_deactivations.
     * @return Value of property phases.
     */
    public ArrayList getSurface_deactivations() {
        return this.surface_deactivations;
    }

    /**
     * Setter for property surface_deactivations.
     * @param phases New value of property phases.
     */
    public void setSurface_deactivations(ArrayList surface_deactivations) {
        this.surface_deactivations = surface_deactivations;
    }

    public final class SurfaceDeactivation {
        
        public SurfaceDeactivation(int phase_id, String phase_name, String phase_html_code,
                double surface_fraction_to_deactivate, double deactivation_time,
                double reactivation_begin_time, double full_reactivation_time) {
            this.phase_id = phase_id;
            this.phase_name = phase_name;
            this.phase_html_code = phase_html_code;
            this.surface_fraction_to_deactivate = surface_fraction_to_deactivate;
            this.deactivation_time = deactivation_time;
            this.reactivation_begin_time = reactivation_begin_time;
            this.full_reactivation_time = full_reactivation_time;
        }
        
        /**
         * Holds value of property phase_id.
         */
        private int phase_id;

        /**
         * Getter for property phase_id.
         * @return Value of property phase_id.
         */
        public int getPhase_id() {
            return this.phase_id;
        }

        /**
         * Setter for property phase_id.
         * @param phase_id New value of property phase_id.
         */
        public void setPhase_id(int phase_id) {
            this.phase_id = phase_id;
        }

        /**
         * Holds value of property phase_name.
         */
        private String phase_name;

        /**
         * Getter for property phase_name.
         * @return Value of property phase_name.
         */
        public String getPhase_name() {
            return this.phase_name;
        }

        /**
         * Setter for property phase_name.
         * @param phase_name New value of property phase_name.
         */
        public void setPhase_name(String phase_name) {
            this.phase_name = phase_name;
        }

        /**
         * Holds value of property phase_html_code.
         */
        private String phase_html_code;

        /**
         * Getter for property phase_html_code.
         * @return Value of property phase_html_code.
         */
        public String getPhase_html_code() {
            return this.phase_html_code;
        }

        /**
         * Setter for property phase_html_code.
         * @param phase_html_code New value of property phase_html_code.
         */
        public void setPhase_html_code(String phase_html_code) {
            this.phase_html_code = phase_html_code;
        }

        /**
         * Holds value of property surface_fraction_to_deactivate.
         */
        private double surface_fraction_to_deactivate;

        /**
         * Getter for property surface_fraction_to_deactivate.
         * @return Value of property surface_fraction_to_deactivate.
         */
        public double getSurface_fraction_to_deactivate() {
            return this.surface_fraction_to_deactivate;
        }

        /**
         * Setter for property surface_fraction_to_deactivate.
         * @param surface_fraction_to_deactivate New value of property surface_fraction_to_deactivate.
         */
        public void setSurface_fraction_to_deactivate(double surface_fraction_to_deactivate) {
            this.surface_fraction_to_deactivate = surface_fraction_to_deactivate;
        }

        /**
         * Holds value of property deactivation_time.
         */
        private double deactivation_time;

        /**
         * Getter for property deactivation_time.
         * @return Value of property deactivation_time.
         */
        public double getDeactivation_time() {
            return this.deactivation_time;
        }

        /**
         * Setter for property deactivation_time.
         * @param deactivation_time New value of property deactivation_time.
         */
        public void setDeactivation_time(double deactivation_time) {
            this.deactivation_time = deactivation_time;
        }

        /**
         * Holds value of property reactivation_begin_time.
         */
        private double reactivation_begin_time;

        /**
         * Getter for property reactivation_begin_time.
         * @return Value of property reactivation_begin_time.
         */
        public double getReactivation_begin_time() {
            return this.reactivation_begin_time;
        }

        /**
         * Setter for property reactivation_begin_time.
         * @param reactivation_begin_time New value of property reactivation_begin_time.
         */
        public void setReactivation_begin_time(double reactivation_begin_time) {
            this.reactivation_begin_time = reactivation_begin_time;
        }

        /**
         * Holds value of property full_reactivation_time.
         */
        private double full_reactivation_time;

        /**
         * Getter for property full_reactivation_time.
         * @return Value of property full_reactivation_time.
         */
        public double getFull_reactivation_time() {
            return this.full_reactivation_time;
        }

        /**
         * Setter for property full_reactivation_time.
         * @param full_reactivation_time New value of property full_reactivation_time.
         */
        public void setFull_reactivation_time(double full_reactivation_time) {
            this.full_reactivation_time = full_reactivation_time;
        }
        
    }

    /**
     * Getter for property surface_deactivation.
     * @return Value of property surface_deactivation.
     */
    public SurfaceDeactivation getSurface_deactivation(int index) {
        return (HydrateMixForm.SurfaceDeactivation)surface_deactivations.get(index);
    }

    /**
     * Holds value of property calorimetry_file.
     */
    private String calorimetry_file;

    /**
     * Getter for property calorimetry_file.
     * @return Value of property calorimetry_file.
     */
    public String getCalorimetry_file() {
        return this.calorimetry_file;
    }

    /**
     * Setter for property calorimetry_file.
     * @param calorimetry_file New value of property calorimetry_file.
     */
    public void setCalorimetry_file(String calorimetry_file) {
        this.calorimetry_file = calorimetry_file;
    }

    /**
     * Holds value of property chemical_shrinkage_file.
     */
    private String chemical_shrinkage_file;

    /**
     * Getter for property chemical_shrinkage_file.
     * @return Value of property chemical_shrinkage_file.
     */
    public String getChemical_shrinkage_file() {
        return this.chemical_shrinkage_file;
    }

    /**
     * Setter for property chemical_shrinkage_file.
     * @param chemical_shrinkage_file New value of property chemical_shrinkage_file.
     */
    public void setChemical_shrinkage_file(String chemical_shrinkage_file) {
        this.chemical_shrinkage_file = chemical_shrinkage_file;
    }

    /**
     * Holds value of property aging_mode.
     */
    private String aging_mode;

    /**
     * Getter for property aging_mode.
     * @return Value of property aging_mode.
     */
    public String getAging_mode() {
        return this.aging_mode;
    }

    /**
     * Setter for property aging_mode.
     * @param aging_mode New value of property aging_mode.
     */
    public void setAging_mode(String aging_mode) {
        this.aging_mode = aging_mode;
    }

    /**
     * Holds value of property calorimetry_temperature.
     */
    private double calorimetry_temperature;

    /**
     * Getter for property calorimetry_temperature.
     * @return Value of property calorimetry_temperature.
     */
    public double getCalorimetry_temperature() {
        return this.calorimetry_temperature;
    }

    /**
     * Setter for property calorimetry_temperature.
     * @param calorimetry_temperature New value of property calorimetry_temperature.
     */
    public void setCalorimetry_temperature(double calorimetry_temperature) {
        this.calorimetry_temperature = calorimetry_temperature;
    }

    /**
     * Holds value of property chemical_shrinkage_temperature.
     */
    private double chemical_shrinkage_temperature;

    /**
     * Getter for property chemical_shrinkage_temperature.
     * @return Value of property chemical_shrinkage_temperature.
     */
    public double getChemical_shrinkage_temperature() {
        return this.chemical_shrinkage_temperature;
    }

    /**
     * Setter for property chemical_shrinkage_temperature.
     * @param chemical_shrinkage_temperature New value of property chemical_shrinkage_temperature.
     */
    public void setChemical_shrinkage_temperature(double chemical_shrinkage_temperature) {
        this.chemical_shrinkage_temperature = chemical_shrinkage_temperature;
    }
}
