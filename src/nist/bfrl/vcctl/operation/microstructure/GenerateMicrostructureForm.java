 /*
  * GenerateMicrostructureForm.java
  *
  * Created on August 31, 2005, 9:23 AM
  */

package nist.bfrl.vcctl.operation.microstructure;

import java.sql.SQLException;
import java.util.logging.Level;
import java.util.logging.Logger;
import nist.bfrl.vcctl.exceptions.*;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.Util;
import org.apache.struts.action.*;

import java.text.*;

import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.util.DefaultNameBuilder;

/**
 * @author tahall
 */
public class GenerateMicrostructureForm extends ActionForm {
    /*
    public GenerateMicrostructureForm(ActionMapping mapping, HttpServletRequest request) {
        reset(mapping, request);
    }
     **/
    
    public GenerateMicrostructureForm() {
    }
    
    public void reset(String userName) throws NoCoarseAggregateException, NoFineAggregateGradingException, NoCoarseAggregateGradingException, NoFineAggregateException, NoCementException, SQLArgumentException, SQLException, NoFlyAshException, NoSlagException, NoInertFillerException, DBFileException {
        
        this.setMix_name(DefaultNameBuilder.buildDefaultOperationNameForUser("MyMix", "", userName));
        particle_specific_gravity=Double.toString(Util.round(Constants.CEMENT_DEFAULT_SPECIFIC_GRAVITY,4));
        rng_seed="0";
        binder_x_dim=Integer.toString(Constants.DEFAULT_BINDER_SYSTEM_DIMENSION);
        binder_y_dim=Integer.toString(Constants.DEFAULT_BINDER_SYSTEM_DIMENSION);
        binder_z_dim=Integer.toString(Constants.DEFAULT_BINDER_SYSTEM_DIMENSION);
        concrete_x_dim=Integer.toString(Constants.DEFAULT_CONCRETE_SYSTEM_DIMENSION);
        concrete_y_dim=Integer.toString(Constants.DEFAULT_CONCRETE_SYSTEM_DIMENSION);
        concrete_z_dim=Integer.toString(Constants.DEFAULT_CONCRETE_SYSTEM_DIMENSION);
        binder_resolution=Double.toString(Util.round(Constants.DEFAULT_BINDER_SYSTEM_RESOLUTION,4)); // microns / pixel
        concrete_resolution = Double.toString(Util.round(Constants.DEFAULT_CONCRETE_SYSTEM_RESOLUTION,4)); // millimeters / pixel
        real_shapes = false;
        flocdegree = "0.0";
        dispersion_distance = "0";
        if (CementDatabase.cementExists(Constants.DEFAULT_CEMENT)) {
            cementName = Constants.DEFAULT_CEMENT;
        } else {
            cementName = CementDatabase.getFirstCementName();
        }

        if (CementDatabase.gradingExists(Constants.DEFAULT_COARSE_GRADING)) {
            coarse_aggregate01_grading_name = Constants.DEFAULT_COARSE_GRADING;
            coarse_aggregate02_grading_name = Constants.DEFAULT_COARSE_GRADING;
        } else {
            coarse_aggregate01_grading_name = CementDatabase.getFirstAggregateGradingNameOfType(Constants.COARSE_AGGREGATE_TYPE);
            coarse_aggregate02_grading_name = CementDatabase.getFirstAggregateGradingNameOfType(Constants.COARSE_AGGREGATE_TYPE);
        }

        if (CementDatabase.gradingExists(Constants.DEFAULT_FINE_GRADING)) {
            fine_aggregate01_grading_name = Constants.DEFAULT_FINE_GRADING;
            fine_aggregate02_grading_name = Constants.DEFAULT_FINE_GRADING;
        } else {
            fine_aggregate01_grading_name = CementDatabase.getFirstAggregateGradingNameOfType(Constants.FINE_AGGREGATE_TYPE);
            fine_aggregate02_grading_name = CementDatabase.getFirstAggregateGradingNameOfType(Constants.FINE_AGGREGATE_TYPE);
        }
        
        add_caco3 = false;
        add_fly_ash = false;
        add_free_lime = false;
        add_inert_filler = false;
        add_silica_fume = false;
        add_slag = false;
        use_own_random_seed = false;
        use_flocculation = false;
        use_dispersion_distance = false;
        
        
        silica_fume_massfrac = Double.toString(0.0);
        silica_fume_volfrac = Double.toString(0.0);
        caco3_massfrac = Double.toString(0.0);
        caco3_volfrac = Double.toString(0.0);
        anhydrite_massfrac = Double.toString(0.0);
        anhydrite_volfrac = Double.toString(0.0);
        dihydrate_massfrac = Double.toString(0.0);
        dihydrate_volfrac = Double.toString(0.0);
        fly_ash_massfrac = Double.toString(0.0);
        fly_ash_volfrac = Double.toString(0.0);
        free_lime_massfrac = Double.toString(0.0);
        free_lime_volfrac = Double.toString(0.0);
        hemihydrate_massfrac = Double.toString(0.0);
        hemihydrate_volfrac = Double.toString(0.0);
        inert_filler_massfrac = Double.toString(0.0);
        inert_filler_volfrac = Double.toString(0.0);
        slag_massfrac = Double.toString(0.0);
        slag_volfrac = Double.toString(0.0);
        
        double cementMassFrac = 1.0;
        double cementVolumeFrac = 1.0;
        cement_massfrac=Double.toString(cementMassFrac);
        cement_volfrac=Double.toString(cementVolumeFrac);
        
        add_coarse_aggregate01 = false;
        add_fine_aggregate01 = false;
        coarse_aggregate01_massfrac = Double.toString(0.0);
        fine_aggregate01_massfrac = Double.toString(0.0);
        coarse_aggregate01_volfrac = Double.toString(0.0);
        fine_aggregate01_volfrac = Double.toString(0.0);
        coarse_aggregate01_name = CementDatabase.getFirstCoarseAggregateName();
        fine_aggregate01_name = CementDatabase.getFirstFineAggregateName();
        coarse_aggregate01_display_name = CementDatabase.getFirstCoarseAggregateDisplayName();
        fine_aggregate01_display_name = CementDatabase.getFirstFineAggregateDisplayName();
        coarse_aggregate01_grading_name = CementDatabase.getFirstCoarseAggregateGradingName();
        fine_aggregate01_grading_name = CementDatabase.getFirstFineAggregateGradingName();
        coarse_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate01_display_name));
        fine_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate01_display_name));
        coarse_aggregate01_grading = CementDatabase.getGrading(coarse_aggregate01_grading_name);
        fine_aggregate01_grading = CementDatabase.getGrading(fine_aggregate01_grading_name);
        coarse_aggregate01_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(coarse_aggregate01_grading_name));
        fine_aggregate01_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(fine_aggregate01_grading_name));
        new_coarse_aggregate01_grading_name = DefaultNameBuilder.buildDefaultMaterialName(Constants.AGGREGATE_TABLE_NAME, Constants.DEFAULT_COARSE_GRADING,".gdg");
        new_fine_aggregate01_grading_name = DefaultNameBuilder.buildDefaultMaterialName(Constants.AGGREGATE_TABLE_NAME, Constants.DEFAULT_FINE_GRADING,".gdg");

        add_coarse_aggregate02 = false;
        add_fine_aggregate02 = false;
        coarse_aggregate02_massfrac = Double.toString(0.0);
        fine_aggregate02_massfrac = Double.toString(0.0);
        coarse_aggregate02_volfrac = Double.toString(0.0);
        fine_aggregate02_volfrac = Double.toString(0.0);
        coarse_aggregate02_name = CementDatabase.getFirstCoarseAggregateName();
        fine_aggregate02_name = CementDatabase.getFirstFineAggregateName();
        coarse_aggregate02_display_name = CementDatabase.getFirstCoarseAggregateDisplayName();
        fine_aggregate02_display_name = CementDatabase.getFirstFineAggregateDisplayName();
        coarse_aggregate02_grading_name = CementDatabase.getFirstCoarseAggregateGradingName();
        fine_aggregate02_grading_name = CementDatabase.getFirstFineAggregateGradingName();
        coarse_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate02_display_name));
        fine_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate02_display_name));
        coarse_aggregate02_grading = CementDatabase.getGrading(coarse_aggregate02_grading_name);
        fine_aggregate02_grading = CementDatabase.getGrading(fine_aggregate02_grading_name);
        coarse_aggregate02_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(coarse_aggregate02_grading_name));
        fine_aggregate02_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(fine_aggregate02_grading_name));
        new_coarse_aggregate02_grading_name = DefaultNameBuilder.buildDefaultMaterialName(Constants.AGGREGATE_TABLE_NAME, Constants.DEFAULT_COARSE_GRADING,".gdg");
        new_fine_aggregate02_grading_name = DefaultNameBuilder.buildDefaultMaterialName(Constants.AGGREGATE_TABLE_NAME, Constants.DEFAULT_FINE_GRADING,".gdg");

        shape_set = Constants.DEFAULT_PARTICLE_SHAPE_SET;
        
        air_volfrac = Double.toString(Util.round(Constants.DEFAULT_AIR_VOLUME_FRACTION,4));

        // Do initial check for the compatibility of the aggregate gradings
        // and the concrete system dimensions and resolution

        try {
            this.updateCoarseAggregate01Grading();
        } catch (SQLArgumentException saes) {
            System.err.println("SQL command argument exception with coarse aggregate 01 grading");
        } catch (SQLException ex) {
            System.err.println("SQL exception with coarse aggregate 01 grading");
        } catch (ParseException ex) {
            ex.printStackTrace();
        }

        try {
            this.updateFineAggregate01Grading();
        } catch (SQLArgumentException saes) {
            System.err.println("SQL command argument exception with fine aggregate 01 grading");
        } catch (SQLException ex) {
            System.err.println("SQL exception with fine aggregate 01 grading");
        } catch (ParseException ex) {
            ex.printStackTrace();
        }

        try {
            this.updateCoarseAggregate02Grading();
        } catch (SQLArgumentException saes) {
            System.err.println("SQL command argument exception with coarse aggregate 02 grading");
        } catch (SQLException ex) {
            System.err.println("SQL exception with coarse aggregate 02 grading");
        } catch (ParseException ex) {
            ex.printStackTrace();
        }

        try {
            this.updateFineAggregate02Grading();
        } catch (SQLArgumentException saes) {
            System.err.println("SQL command argument exception with fine aggregate 02 grading");
        } catch (SQLException ex) {
            System.err.println("SQL exception with fine aggregate 02 grading");
        } catch (ParseException ex) {
            ex.printStackTrace();
        }

        // Set the initial characteristics files
        java.util.List<String> l = CementDatabase.getFlyAshNames();
        if (!l.isEmpty()) {
            this.setFly_ash_psd(l.get(0));
            updateFlyAshSpecificGravity();
        } else {
            this.setFly_ash_psd("");
            fly_ash_sg = String.valueOf(Constants.FLY_ASH_DEFAULT_SPECIFIC_GRAVITY);
        }
        l.clear();
        l = CementDatabase.getSlagNames();
        if (!l.isEmpty()) {
            this.setSlag_psd(l.get(0));
            updateSlagSpecificGravity();
        } else {
            this.setSlag_psd("");
            slag_sg = String.valueOf(Constants.SLAG_DEFAULT_SPECIFIC_GRAVITY);
        }
        l.clear();
        l = CementDatabase.getInertFillerNames();
        if (!l.isEmpty()) {
            this.setInert_filler_psd(l.get(0));
            updateInertFillerSpecificGravity();
        } else {
            this.setInert_filler_psd("");
            inert_filler_sg = String.valueOf(Constants.INERT_FILLER_DEFAULT_SPECIFIC_GRAVITY);
        }
        
        // water_cement_ratio="0.3125";
        
        // NumberFormat frac_format = new DecimalFormat("0.000000000");
        // double massfrac = 3.2/(3.2+Constants.waterDensity);
        
        double waterBinderRatio = 0.45;
        water_binder_ratio = Double.toString(waterBinderRatio);
        double binderMassFrac = 1/(waterBinderRatio+1);
        binder_massfrac=Double.toString(Util.round(binderMassFrac,4));
        double waterMassFrac = waterBinderRatio/(waterBinderRatio+1);
        water_massfrac=Double.toString(Util.round(waterMassFrac,4));
        
        
        slag_sample = "not present";
        fly_ash_sample = "not present";
        
        this.setNotes("");
        String cementPSD;
        cementPSD = CementDatabase.getCementPSD(cementName);
        this.setAnhydrite_psd(cementPSD);
        this.setCaco3_psd(cementPSD);
        this.setDihydrate_psd(cementPSD);
        
        this.setFree_lime_psd(cementPSD);
        this.setHemihydrate_psd(cementPSD);
        this.setSilica_fume_psd(cementPSD);
        
        this.setFraction_orthorombic_c3a("0.0");

        try {
            this.updateFractions();
        } catch (ParseException ex) {
           ex.printStackTrace();
        }

        try {
            this.updateSulfateFractionsGivenCement(cementName);
        } catch (ParseException ex) {
            ex.printStackTrace();
        }
        
        // Verify that's correct
        /*
        double cementSpecificGravity = this.calculateCementSpecificGravity();
        double binderSpecificGravity = (cementVolumeFrac/cementMassFrac)*cementSpecificGravity;
        double binderVolFrac = binderMassFrac/(binderMassFrac*(1-binderSpecificGravity) + binderSpecificGravity);
        binder_volfrac = Double.toString(binderVolFrac);
        double waterVolFrac = (waterMassFrac * binderSpecificGravity)/(1 + waterMassFrac * (binderSpecificGravity - 1));
        water_volfrac = Double.toString(waterVolFrac);
         **/

        try {
            this.updateMixVolumeFractions();
        } catch (ParseException ex) {
            ex.printStackTrace();
        }

        total_massfrac=Double.toString(1.0);
        total_volfrac=Double.toString(1.0);
        
        /*
        // Added
        this.setPsd_selected(cement_psd);
         
        this.updateFractions();*/
    }
    
    public String getFlyAshPhaseDistributionInput() throws SQLException, SQLArgumentException, DBFileException {
        String flyash_name = this.getFly_ash_psd();
        FlyAsh f = FlyAsh.load(flyash_name);
        
        StringBuffer buf = new StringBuffer();
        
        buf.append(Integer.toString(f.getDistribute_phases_by())+"\n");
        
        buf.append(Double.toString(f.getAluminosilicate_glass_fraction())+"\n");
        buf.append(Double.toString(f.getCalcium_aluminum_disilicate_fraction())+"\n");
        buf.append(Double.toString(f.getTricalcium_aluminate_fraction())+"\n");
        buf.append(Double.toString(f.getCalcium_chloride_fraction())+"\n");
        buf.append(Double.toString(f.getSilica_fraction())+"\n");
        buf.append(Double.toString(f.getAnhydrite_fraction())+"\n");
        
        return buf.toString();
    }
    
    
    
    public static GenerateMicrostructureForm create_from_state(String name, String userName) throws SQLException, SQLArgumentException {
        Operation op = OperationDatabase.getOperationForUser(name,userName);
        if (op != null) {
            byte[] imxml = op.getState();
            return (GenerateMicrostructureForm)OperationState.restore_from_Xml(imxml);
        } else {
            return null;
        }
    }
    
    /**
     * Holds value of property mix_name.
     */
    private String mix_name;
    
    /**
     * Holds value of property particle_specific_gravity.
     */
    private String particle_specific_gravity;
    
    /**
     * Holds value of property rng_seed.
     */
    private String rng_seed;
    
    /**
     * Holds value of property binder_x_dim.
     */
    private String binder_x_dim;
    
    /**
     * Holds value of property binder_y_dim.
     */
    private String binder_y_dim;
    
    /**
     * Holds value of property binder_z_dim.
     */
    private String binder_z_dim;
    
    /**
     * Holds value of property binder_resolution.
     */
    private String binder_resolution;
    
    /**
     * Holds value of property real_shapes.
     */
    private boolean real_shapes;
    
    /**
     * Holds value of property shape_set.
     */
    private String shape_set;
    
    /**
     * Holds value of property flocdegree.
     */
    private String flocdegree;
    
    /**
     * Holds value of property dispersion_distance.
     */
    private String dispersion_distance;
    
    /**
     * Holds value of property cementName.
     */
    private String cementName;
    
    /**
     * Holds value of property water_cement_ratio.
     */
    /*
    private String water_cement_ratio;
     **/
    
    /**
     * Holds value of property binder_massfrac.
     */
    private String binder_massfrac;
    
    /**
     * Holds value of property binder_volfrac.
     */
    private String binder_volfrac;
    
    /**
     * Holds value of property silica_fume_massfrac.
     */
    private String silica_fume_massfrac;
    
    /**
     * Holds value of property silica_fume_volfrac.
     */
    private String silica_fume_volfrac;
    
    /**
     * Holds value of property fly_ash_massfrac.
     */
    private String fly_ash_massfrac;
    
    /**
     * Holds value of property fly_ash_volfrac.
     */
    private String fly_ash_volfrac;
    
    /**
     * Holds value of property slag_massfrac.
     */
    private String slag_massfrac;
    
    /**
     * Holds value of property slag_volfrac.
     */
    private String slag_volfrac;
    
    /**
     * Holds value of property caco3_massfrac.
     */
    private String caco3_massfrac;
    
    /**
     * Holds value of property caco3_volfrac.
     */
    private String caco3_volfrac;
    
    /**
     * Holds value of property free_lime_massfrac.
     */
    private String free_lime_massfrac;
    
    /**
     * Holds value of property free_lime_volfrac.
     */
    private String free_lime_volfrac;
    
    /**
     * Holds value of property inert_filler_massfrac.
     */
    private String inert_filler_massfrac;
    
    /**
     * Holds value of property inert_filler_volfrac.
     */
    private String inert_filler_volfrac;
    
    /**
     * Holds value of property dihydrate_massfrac.
     */
    private String dihydrate_massfrac;
    
    /**
     * Holds value of property dihydrate_volfrac.
     */
    private String dihydrate_volfrac;
    
    /**
     * Holds value of property anhydrite_massfrac.
     */
    private String anhydrite_massfrac;
    
    /**
     * Holds value of property anhydrite_volfrac.
     */
    private String anhydrite_volfrac;
    
    /**
     * Holds value of property hemihydrate_massfrac.
     */
    private String hemihydrate_massfrac;
    
    /**
     * Holds value of property hemihydrate_volfrac.
     */
    private String hemihydrate_volfrac;
    
    /**
     * Holds value of property water_massfrac.
     */
    private String water_massfrac;
    
    /**
     * Holds value of property water_volfrac.
     */
    private String water_volfrac;
    
    /**
     * Holds value of property total_massfrac.
     */
    private String total_massfrac;
    
    /**
     * Holds value of property total_volfrac.
     */
    private String total_volfrac;
    
    /**
     * Holds value of property anhydrite_psd.
     */
    private String anhydrite_psd;
    
    /**
     * Holds value of property caco3_psd.
     */
    private String caco3_psd;
    
    /**
     * Holds value of property dihydrate_psd.
     */
    private String dihydrate_psd;
    
    /**
     * Holds value of property fly_ash_psd.
     */
    private String fly_ash_psd;
    
    /**
     * Holds value of property free_lime_psd.
     */
    private String free_lime_psd;
    
    /**
     * Holds value of property hemihydrate_psd.
     */
    private String hemihydrate_psd;
    
    /**
     * Holds value of property inert_filler_psd.
     */
    private String inert_filler_psd;
    
    /**
     * Holds value of property silica_fume_psd.
     */
    private String silica_fume_psd;
    
    /**
     * Holds value of property slag_psd.
     */
    private String slag_psd;
    
    /**
     * Holds value of property cement_sample.
     */
    private String cement_sample;
    
    /**
     * Holds value of property silica_fume_sample.
     */
    private String silica_fume_sample;
    
    /**
     * Holds value of property fly_ash_sample.
     */
    private String fly_ash_sample;
    
    /**
     * Holds value of property slag_sample.
     */
    private String slag_sample;
    
    /**
     * Holds value of property caco3_sample.
     */
    private String caco3_sample;
    
    /**
     * Holds value of property free_lime_sample.
     */
    private String free_lime_sample;
    
    /**
     * Holds value of property inert_filler_sample.
     */
    private String inert_filler_sample;
    
    /**
     * Holds value of property dihydrate_sample.
     */
    private String dihydrate_sample;
    
    /**
     * Holds value of property anhydrite_sample.
     */
    private String anhydrite_sample;
    
    /**
     * Holds value of property hemihydrate_sample.
     */
    private String hemihydrate_sample;
    
    /**
     * Holds value of property coarse_aggregate01_massfrac.
     */
    private String coarse_aggregate01_massfrac;
    
    /**
     * Holds value of property fine_aggregate01_massfrac.
     */
    private String fine_aggregate01_massfrac;
    
    /**
     * Holds value of property coarse_aggregate01_name.
     */
    private String coarse_aggregate01_name;
    
    /**
     * Holds value of property fine_aggregate01_name.
     */
    private String fine_aggregate01_name;

     /**
     * Holds value of property coarse_aggregate01_display_name.
     */
    private String coarse_aggregate01_display_name;

    /**
     * Holds value of property fine_aggregate01_display_name.
     */
    private String fine_aggregate01_display_name;

     /**
     * Holds value of property coarse_aggregate02_massfrac.
     */
    private String coarse_aggregate02_massfrac;

    /**
     * Holds value of property fine_aggregate02_massfrac.
     */
    private String fine_aggregate02_massfrac;

    /**
     * Holds value of property coarse_aggregate02_name.
     */
    private String coarse_aggregate02_name;

    /**
     * Holds value of property fine_aggregate02_name.
     */
    private String fine_aggregate02_name;

     /**
     * Holds value of property coarse_aggregate02_display_name.
     */
    private String coarse_aggregate02_display_name;

    /**
     * Holds value of property fine_aggregate02_display_name.
     */
    private String fine_aggregate02_display_name;

    
    public String getCoarse_aggregate01_massfrac() {
        return coarse_aggregate01_massfrac;
    }
    
    public void setCoarse_aggregate01_massfrac(String coarse_aggregate01_massfrac) {
        this.coarse_aggregate01_massfrac = coarse_aggregate01_massfrac;
    }
    
    public String getFine_aggregate01_massfrac() {
        return fine_aggregate01_massfrac;
    }
    
    public void setFine_aggregate01_massfrac(String fine_aggregate01_massfrac) {
        this.fine_aggregate01_massfrac = fine_aggregate01_massfrac;
    }

    public String getCoarse_aggregate01_name() {
        return coarse_aggregate01_name;
    }

    public void setCoarse_aggregate01_name(String coarse_aggregate01_name) {
        this.coarse_aggregate01_name = coarse_aggregate01_name;
    }
    
    public String getFine_aggregate01_name() {
        return fine_aggregate01_name;
    }
    
    public void setFine_aggregate01_name(String fine_aggregate01_name) {
        this.fine_aggregate01_name = fine_aggregate01_name;
    }

    public String getCoarse_aggregate01_display_name() {
        return coarse_aggregate01_display_name;
    }

    public void setCoarse_aggregate01_display_name(String coarse_aggregate01_display_name) {
        this.coarse_aggregate01_display_name = coarse_aggregate01_display_name;
    }

    public String getFine_aggregate01_display_name() {
        return fine_aggregate01_display_name;
    }

    public void setFine_aggregate01_display_name(String fine_aggregate01_display_name) {
        this.fine_aggregate01_display_name = fine_aggregate01_display_name;
    }
    
    public String getCoarse_aggregate02_massfrac() {
        return coarse_aggregate02_massfrac;
    }

    public void setCoarse_aggregate02_massfrac(String coarse_aggregate02_massfrac) {
        this.coarse_aggregate02_massfrac = coarse_aggregate02_massfrac;
    }

    public String getFine_aggregate02_massfrac() {
        return fine_aggregate02_massfrac;
    }

    public void setFine_aggregate02_massfrac(String fine_aggregate02_massfrac) {
        this.fine_aggregate02_massfrac = fine_aggregate02_massfrac;
    }

    public String getCoarse_aggregate02_name() {
        return coarse_aggregate02_name;
    }

    public void setCoarse_aggregate02_name(String coarse_aggregate02_name) {
        this.coarse_aggregate02_name = coarse_aggregate02_name;
    }

    public String getFine_aggregate02_name() {
        return fine_aggregate02_name;
    }

    public void setFine_aggregate02_name(String fine_aggregate02_name) {
        this.fine_aggregate02_name = fine_aggregate02_name;
    }

    public String getCoarse_aggregate02_display_name() {
        return coarse_aggregate02_display_name;
    }

    public void setCoarse_aggregate02_display_name(String coarse_aggregate02_display_name) {
        this.coarse_aggregate02_display_name = coarse_aggregate02_display_name;
    }

    public String getFine_aggregate02_display_name() {
        return fine_aggregate02_display_name;
    }

    public void setFine_aggregate02_display_name(String fine_aggregate02_display_name) {
        this.fine_aggregate02_display_name = fine_aggregate02_display_name;
    }

    /**
     * Getter for property filename.
     * @return Value of property filename.
     */
    public String getMix_name()  {
        return this.mix_name;
    }
    
    /**
     * Setter for property filename.
     * @param filename New value of property filename.
     */
    public void setMix_name(java.lang.String mix_name)  {
        this.mix_name = mix_name;
    }
    
    /**
     * Getter for property particleSpecificGravity.
     * @return Value of property particleSpecificGravity.
     */
    public String getParticle_specific_gravity()  {
        
        return this.particle_specific_gravity;
    }
    
    /**
     * Setter for property particleSpecificGravity.
     * @param particleSpecificGravity New value of property particleSpecificGravity.
     */
    public void setParticle_specific_gravity(java.lang.String particle_specific_gravity)  {
        
        this.particle_specific_gravity = particle_specific_gravity;
    }
    
    /**
     * Getter for property rngSeed.
     * @return Value of property rngSeed.
     */
    public String getRng_seed()  {
        
        return this.rng_seed;
    }
    
    /**
     * Setter for property rngSeed.
     * @param rngSeed New value of property rngSeed.
     */
    public void setRng_seed(java.lang.String rng_seed)  {
        
        this.rng_seed = rng_seed;
    }
    
    /**
     * Getter for property xdim.
     * @return Value of property xdim.
     */
    public String getBinder_x_dim()  {
        return this.binder_x_dim;
    }
    
    /**
     * Setter for property xdim.
     * @param xdim New value of property xdim.
     */
    public void setBinder_x_dim(java.lang.String binder_x_dim)  {
        this.binder_x_dim = binder_x_dim;
    }
    
    /**
     * Getter for property ydim.
     * @return Value of property ydim.
     */
    public String getBinder_y_dim()  {
        return this.binder_y_dim;
    }
    
    /**
     * Setter for property ydim.
     * @param ydim New value of property ydim.
     */
    public void setBinder_y_dim(java.lang.String binder_y_dim)  {
        this.binder_y_dim = binder_y_dim;
    }
    
    /**
     * Getter for property zdim.
     * @return Value of property zdim.
     */
    public String getBinder_z_dim()  {
        return this.binder_z_dim;
    }
    
    /**
     * Setter for property zdim.
     * @param zdim New value of property zdim.
     */
    public void setBinder_z_dim(java.lang.String binder_z_dim)  {
        this.binder_z_dim = binder_z_dim;
    }
    
    /**
     * Getter for property resolution.
     * @return Value of property resolution.
     */
    public String getBinder_resolution() {
        return this.binder_resolution;
    }
    
    /**
     * Setter for property resolution.
     * @param resolution New value of property resolution.
     */
    public void setBinder_resolution(String binder_resolution) {
        this.binder_resolution = binder_resolution;
    }
    
    /**
     * Getter for property real_shapes.
     * @return Value of property real_shapes.
     */
    public boolean isReal_shapes() {
        
        return this.real_shapes;
    }
    
    /**
     * Setter for property real_shapes.
     * @param real_shapes New value of property real_shapes.
     */
    public void setReal_shapes(boolean real_shapes) {
        
        this.real_shapes = real_shapes;
    }
    
    /**
     * Getter for property shape_set.
     * @return Value of property shape_set.
     */
    public String getShape_set() {
        
        return this.shape_set;
    }
    
    /**
     * Setter for property shape_set.
     * @param shape_set New value of property shape_set.
     */
    public void setShape_set(String shape_set) {
        
        this.shape_set = shape_set;
    }
    
    /**
     * Getter for property flocdegree.
     * @return Value of property flocdegree.
     */
    public String getFlocdegree() {
        
        return this.flocdegree;
    }
    
    /**
     * Setter for property flocdegree.
     * @param flocdegree New value of property flocdegree.
     */
    public void setFlocdegree(String flocdegree) {
        
        this.flocdegree = flocdegree;
    }
    
    /**
     * Getter for property dispersion_distance.
     * @return Value of property dispersion_distance.
     */
    public String getDispersion_distance() {
        
        return this.dispersion_distance;
    }
    
    /**
     * Setter for property dispersion_distance.
     * @param dispersion_distance New value of property dispersion_distance.
     */
    public void setDispersion_distance(String dispersion_distance) {
        
        this.dispersion_distance = dispersion_distance;
    }
    
    /**
     * Getter for property cement_psd.
     * @return Value of property cement_psd.
     */
    public String getCementName() {
        return this.cementName;
    }
    
    /**
     * Setter for property cement_psd.
     * @param cement_psd_file New value of property cement_psd.
     */
    public void setCementName(String cementName) {
        this.cementName = cementName;
    }
    
    /**
     * Getter for property water_cement_ratio.
     * @return Value of property water_cement_ratio.
     */
    /*
    public String getWater_cement_ratio() {
     
        return this.water_cement_ratio;
    }
     **/
    
    /**
     * Setter for property water_cement_ratio.
     * @param water_cement_ratio New value of property water_cement_ratio.
     */
    /*
    public void setWater_cement_ratio(String water_cement_ratio) {
     
        this.water_cement_ratio = water_cement_ratio;
    }
     **/
    
    /**
     * Getter for property binder_massfrac.
     * @return Value of property binder_massfrac.
     */
    public String getBinder_massfrac() {
        
        return this.binder_massfrac;
    }
    
    /**
     * Setter for property binder_massfrac.
     * @param binder_massfrac New value of property binder_massfrac.
     */
    public void setBinder_massfrac(String binder_massfrac) {
        
        this.binder_massfrac = binder_massfrac;
    }
    
    /**
     * Getter for property binder_volfrac.
     * @return Value of property binder_volfrac.
     */
    public String getBinder_volfrac() {
        
        return this.binder_volfrac;
    }
    
    /**
     * Setter for property binder_volfrac.
     * @param binder_volfrac New value of property binder_volfrac.
     */
    public void setBinder_volfrac(String binder_volfrac) {
        
        this.binder_volfrac = binder_volfrac;
    }
    
    /**
     * Getter for property silica_fume_massfrac.
     * @return Value of property silica_fume_massfrac.
     */
    public String getSilica_fume_massfrac() {
        
        return this.silica_fume_massfrac;
    }
    
    /**
     * Setter for property silica_fume_massfrac.
     * @param silica_fume_massfrac New value of property silica_fume_massfrac.
     */
    public void setSilica_fume_massfrac(String silica_fume_massfrac) {
        
        this.silica_fume_massfrac = silica_fume_massfrac;
    }
    
    /**
     * Getter for property silica_fume_volfrac.
     * @return Value of property silica_fume_volfrac.
     */
    public String getSilica_fume_volfrac() {
        
        return this.silica_fume_volfrac;
    }
    
    /**
     * Setter for property silica_fume_volfrac.
     * @param silica_fume_volfrac New value of property silica_fume_volfrac.
     */
    public void setSilica_fume_volfrac(String silica_fume_volfrac) {
        
        this.silica_fume_volfrac = silica_fume_volfrac;
    }
    
    /**
     * Getter for property fly_ash_massfrac.
     * @return Value of property fly_ash_massfrac.
     */
    public String getFly_ash_massfrac() {
        
        return this.fly_ash_massfrac;
    }
    
    /**
     * Return the fly ash mass fraction as a double for use outside of the
     * form
     */
    public double get_fly_ash_massfrac() {
        double dval = 0.0;
        
        try {
            dval = Double.parseDouble(getFly_ash_massfrac());
        } catch (NumberFormatException nfe) {
            dval = 0.0;
        // } catch (ParseException ex) {
        //    dval = 0.0;
        }
        return dval;
    }
    
    /**
     * Return the slag mass fraction as a double for use outside of the
     * form
     */
    public double get_slag_massfrac() {
        double dval = 0.0;
        
        try {
            dval = Double.parseDouble(getSlag_massfrac());
        } catch (NumberFormatException nfe) {
            dval = 0.0;
        // } catch (ParseException ex) {
        //     dval = 0.0;
        }
        return dval;
    }
    
    /**
     * Return the filler mass fraction as a double for use outside of the
     * form
     */
    public double get_inert_filler_massfrac() {
        double dval = 0.0;
        
        try {
            dval = Double.parseDouble(getInert_filler_massfrac());
        } catch (NumberFormatException nfe) {
            dval = 0.0;
        // } catch (ParseException ex) {
        //     dval = 0.0;
        }
        return dval;
    }
    
    /**
     * Setter for property fly_ash_massfrac.
     * @param fly_ash_massfrac New value of property fly_ash_massfrac.
     */
    public void setFly_ash_massfrac(String fly_ash_massfrac) {
        
        this.fly_ash_massfrac = fly_ash_massfrac;
    }
    
    /**
     * Getter for property fly_ash_volfrac.
     * @return Value of property fly_ash_volfrac.
     */
    public String getFly_ash_volfrac() {
        
        return this.fly_ash_volfrac;
    }
    
    /**
     * Setter for property fly_ash_volfrac.
     * @param fly_ash_volfrac New value of property fly_ash_volfrac.
     */
    public void setFly_ash_volfrac(String fly_ash_volfrac) {
        
        this.fly_ash_volfrac = fly_ash_volfrac;
    }
    
    /**
     * Getter for property slag_massfrac.
     * @return Value of property slag_massfrac.
     */
    public String getSlag_massfrac() {
        
        return this.slag_massfrac;
    }
    
    /**
     * Setter for property slag_massfrac.
     * @param slag_massfrac New value of property slag_massfrac.
     */
    public void setSlag_massfrac(String slag_massfrac) {
        
        this.slag_massfrac = slag_massfrac;
    }
    
    /**
     * Getter for property slag_volfrac.
     * @return Value of property slag_volfrac.
     */
    public String getSlag_volfrac() {
        
        return this.slag_volfrac;
    }
    
    /**
     * Setter for property slag_volfrac.
     * @param slag_volfrac New value of property slag_volfrac.
     */
    public void setSlag_volfrac(String slag_volfrac) {
        
        this.slag_volfrac = slag_volfrac;
    }
    
    /**
     * Getter for property caco3_massfrac.
     * @return Value of property caco3_massfrac.
     */
    public String getCaco3_massfrac() {
        
        return this.caco3_massfrac;
    }
    
    /**
     * Setter for property caco3_massfrac.
     * @param caco3_massfrac New value of property caco3_massfrac.
     */
    public void setCaco3_massfrac(String caco3_massfrac) {
        
        this.caco3_massfrac = caco3_massfrac;
    }
    
    /**
     * Getter for property caco3_volfrac.
     * @return Value of property caco3_volfrac.
     */
    public String getCaco3_volfrac() {
        
        return this.caco3_volfrac;
    }
    
    /**
     * Setter for property caco3_volfrac.
     * @param caco3_volfrac New value of property caco3_volfrac.
     */
    public void setCaco3_volfrac(String caco3_volfrac) {
        
        this.caco3_volfrac = caco3_volfrac;
    }
    
    /**
     * Getter for property free_lime_massfrac.
     * @return Value of property free_lime_massfrac.
     */
    public String getFree_lime_massfrac() {
        
        return this.free_lime_massfrac;
    }
    
    /**
     * Setter for property free_lime_massfrac.
     * @param free_lime_massfrac New value of property free_lime_massfrac.
     */
    public void setFree_lime_massfrac(String free_lime_massfrac) {
        
        this.free_lime_massfrac = free_lime_massfrac;
    }
    
    /**
     * Getter for property free_lime_volfrac.
     * @return Value of property free_lime_volfrac.
     */
    public String getFree_lime_volfrac() {
        
        return this.free_lime_volfrac;
    }
    
    /**
     * Setter for property free_lime_volfrac.
     * @param free_lime_volfrac New value of property free_lime_volfrac.
     */
    public void setFree_lime_volfrac(String free_lime_volfrac) {
        
        this.free_lime_volfrac = free_lime_volfrac;
    }
    
    /**
     * Getter for property inert_filler_massfrac.
     * @return Value of property inert_filler_massfrac.
     */
    public String getInert_filler_massfrac() {
        
        return this.inert_filler_massfrac;
    }
    
    /**
     * Setter for property inert_filler_massfrac.
     * @param inert_filler_massfrac New value of property inert_filler_massfrac.
     */
    public void setInert_filler_massfrac(String inert_filler_massfrac) {
        
        this.inert_filler_massfrac = inert_filler_massfrac;
    }
    
    /**
     * Getter for property inert_filler_volfrac.
     * @return Value of property inert_filler_volfrac.
     */
    public String getInert_filler_volfrac() {
        
        return this.inert_filler_volfrac;
    }
    
    /**
     * Setter for property inert_filler_volfrac.
     * @param inert_filler_volfrac New value of property inert_filler_volfrac.
     */
    public void setInert_filler_volfrac(String inert_filler_volfrac) {
        
        this.inert_filler_volfrac = inert_filler_volfrac;
    }
    
    /**
     * Getter for property dihydrate_massfrac.
     * @return Value of property dihydrate_massfrac.
     */
    public String getDihydrate_massfrac() {
        
        return this.dihydrate_massfrac;
    }
    
    /**
     * Setter for property dihydrate_massfrac.
     * @param dihydrate_massfrac New value of property dihydrate_massfrac.
     */
    public void setDihydrate_massfrac(String dihydrate_massfrac) {
        
        this.dihydrate_massfrac = dihydrate_massfrac;
    }
    
    /**
     * Getter for property dihydrate_volfrac.
     * @return Value of property dihydrate_volfrac.
     */
    public String getDihydrate_volfrac() {
        
        return this.dihydrate_volfrac;
    }
    
    /**
     * Setter for property dihydrate_volfrac.
     * @param dihydrate_volfrac New value of property dihydrate_volfrac.
     */
    public void setDihydrate_volfrac(String dihydrate_volfrac) {
        
        this.dihydrate_volfrac = dihydrate_volfrac;
    }
    
    /**
     * Getter for property anhydrite_massfrac.
     * @return Value of property anhydrite_massfrac.
     */
    public String getAnhydrite_massfrac() {
        
        return this.anhydrite_massfrac;
    }
    
    /**
     * Setter for property anhydrite_massfrac.
     * @param anhydrite_massfrac New value of property anhydrite_massfrac.
     */
    public void setAnhydrite_massfrac(String anhydrite_massfrac) {
        
        this.anhydrite_massfrac = anhydrite_massfrac;
    }
    
    /**
     * Getter for property anhydrite_volfrac.
     * @return Value of property anhydrite_volfrac.
     */
    public String getAnhydrite_volfrac() {
        
        return this.anhydrite_volfrac;
    }
    
    /**
     * Setter for property anhydrite_volfrac.
     * @param anhydrite_volfrac New value of property anhydrite_volfrac.
     */
    public void setAnhydrite_volfrac(String anhydrite_volfrac) {
        
        this.anhydrite_volfrac = anhydrite_volfrac;
    }
    
    /**
     * Getter for property hemihydrate_massfrac.
     * @return Value of property hemihydrate_massfrac.
     */
    public String getHemihydrate_massfrac() {
        
        return this.hemihydrate_massfrac;
    }
    
    /**
     * Setter for property hemihydrate_massfrac.
     * @param hemihydrate_massfrac New value of property hemihydrate_massfrac.
     */
    public void setHemihydrate_massfrac(String hemihydrate_massfrac) {
        
        this.hemihydrate_massfrac = hemihydrate_massfrac;
    }
    
    /**
     * Getter for property hemihydrate_volfrac.
     * @return Value of property hemihydrate_volfrac.
     */
    public String getHemihydrate_volfrac() {
        
        return this.hemihydrate_volfrac;
    }
    
    /**
     * Setter for property hemihydrate_volfrac.
     * @param hemihydrate_volfrac New value of property hemihydrate_volfrac.
     */
    public void setHemihydrate_volfrac(String hemihydrate_volfrac) {
        
        this.hemihydrate_volfrac = hemihydrate_volfrac;
    }
    
    /**
     * Getter for property water_massfrac.
     * @return Value of property water_massfrac.
     */
    public String getWater_massfrac() {
        
        return this.water_massfrac;
    }
    
    /**
     * Setter for property water_massfrac.
     * @param water_massfrac New value of property water_massfrac.
     */
    public void setWater_massfrac(String water_massfrac) {
        
        this.water_massfrac = water_massfrac;
    }
    
    /**
     * Getter for property water_volfrac.
     * @return Value of property water_volfrac.
     */
    public String getWater_volfrac() {
        
        return this.water_volfrac;
    }
    
    /**
     * Setter for property water_volfrac.
     * @param water_volfrac New value of property water_volfrac.
     */
    public void setWater_volfrac(String water_volfrac) {
        
        this.water_volfrac = water_volfrac;
    }
    
    /**
     * Getter for property total_massfrac.
     * @return Value of property total_massfrac.
     */
    public String getTotal_massfrac() {
        
        return this.total_massfrac;
    }
    
    /**
     * Setter for property total_massfrac.
     * @param total_massfrac New value of property total_massfrac.
     */
    public void setTotal_massfrac(String total_massfrac) {
        
        this.total_massfrac = total_massfrac;
    }
    
    /**
     * Getter for property total_volfrac.
     * @return Value of property total_volfrac.
     */
    public String getTotal_volfrac() {
        
        return this.total_volfrac;
    }
    
    /**
     * Setter for property total_volfrac.
     * @param total_volfrac New value of property total_volfrac.
     */
    public void setTotal_volfrac(String total_volfrac) {
        
        this.total_volfrac = total_volfrac;
    }
    
    /**
     * Getter for property anhydrite_psd.
     * @return Value of property anhydrite_psd.
     */
    public String getAnhydrite_psd() {
        
        return this.anhydrite_psd;
    }
    
    /**
     * Setter for property anhydrite_psd.
     * @param anhydrite_psd New value of property anhydrite_psd.
     */
    public void setAnhydrite_psd(String anhydrite_psd) {
        
        this.anhydrite_psd = anhydrite_psd;
    }
    
    /**
     * Getter for property caco3_psd.
     * @return Value of property caco3_psd.
     */
    public String getCaco3_psd() {
        
        return this.caco3_psd;
    }
    
    /**
     * Setter for property caco3_psd.
     * @param caco3_psd New value of property caco3_psd.
     */
    public void setCaco3_psd(String caco3_psd) {
        
        this.caco3_psd = caco3_psd;
    }
    
    /**
     * Getter for property dihydrate_psd.
     * @return Value of property dihydrate_psd.
     */
    public String getDihydrate_psd() {
        
        return this.dihydrate_psd;
    }
    
    /**
     * Setter for property dihydrate_psd.
     * @param dihydrate_psd New value of property dihydrate_psd.
     */
    public void setDihydrate_psd(String dihydrate_psd) {
        
        this.dihydrate_psd = dihydrate_psd;
    }
    
    /**
     * Getter for property fly_ash_psd.
     * @return Value of property fly_ash_psd.
     */
    public String getFly_ash_psd() {
        
        return this.fly_ash_psd;
    }
    
    /**
     * Setter for property fly_ash_psd.
     * @param fly_ash_psd New value of property fly_ash_psd.
     */
    public void setFly_ash_psd(String fly_ash_psd) {
        
        this.fly_ash_psd = fly_ash_psd;
    }
    
    /**
     * Getter for property free_lime_psd.
     * @return Value of property free_lime_psd.
     */
    public String getFree_lime_psd() {
        
        return this.free_lime_psd;
    }
    
    /**
     * Setter for property free_lime_psd.
     * @param free_lime_psd New value of property free_lime_psd.
     */
    public void setFree_lime_psd(String free_lime_psd) {
        
        this.free_lime_psd = free_lime_psd;
    }
    
    /**
     * Getter for property hemihydrate_psd.
     * @return Value of property hemihydrate_psd.
     */
    public String getHemihydrate_psd() {
        
        return this.hemihydrate_psd;
    }
    
    /**
     * Setter for property hemihydrate_psd.
     * @param hemihydrate_psd New value of property hemihydrate_psd.
     */
    public void setHemihydrate_psd(String hemihydrate_psd) {
        
        this.hemihydrate_psd = hemihydrate_psd;
    }
    
    /**
     * Getter for property inert_filler_psd.
     * @return Value of property inert_filler_psd.
     */
    public String getInert_filler_psd() {
        
        return this.inert_filler_psd;
    }
    
    /**
     * Setter for property inert_filler_psd.
     * @param inert_filler_psd New value of property inert_filler_psd.
     */
    public void setInert_filler_psd(String inert_filler_psd) {
        
        this.inert_filler_psd = inert_filler_psd;
    }
    
    /**
     * Getter for property silica_fume_psd.
     * @return Value of property silica_fume_psd.
     */
    public String getSilica_fume_psd() {
        
        return this.silica_fume_psd;
    }
    
    /**
     * Setter for property silica_fume_psd.
     * @param silica_fume_psd New value of property silica_fume_psd.
     */
    public void setSilica_fume_psd(String silica_fume_psd) {
        
        this.silica_fume_psd = silica_fume_psd;
    }
    
    /**
     * Getter for property slag_psd.
     * @return Value of property slag_psd.
     */
    public String getSlag_psd() {
        
        return this.slag_psd;
    }
    
    /**
     * Setter for property slag_psd.
     * @param slag_psd New value of property slag_psd.
     */
    public void setSlag_psd(String slag_psd) {
        
        this.slag_psd = slag_psd;
    }
    
    /**
     * Getter for property cement_sample.
     * @return Value of property cement_sample.
     */
    public String getCement_sample()  {
        
        return this.cement_sample;
    }
    
    /**
     * Setter for property cement_sample.
     * @param cement New value of property cement_sample.
     */
    public void setCement_sample(String cement_sample)  {
        
        this.cement_sample = cement_sample;
    }
    
    /**
     * Getter for property silica_fume_sample.
     * @return Value of property silica_fume_sample.
     */
    public String getSilica_fume_sample()  {
        
        return this.silica_fume_sample;
    }
    
    /**
     * Setter for property silica_fume_sample.
     * @param pozzolan New value of property silica_fume_sample.
     */
    public void setSilica_fume_sample(String silica_fume_sample)  {
        
        this.silica_fume_sample = silica_fume_sample;
    }
    
    /**
     * Getter for property fly_ash_sample.
     * @return Value of property fly_ash_sample.
     */
    public String getFly_ash_sample()   {
        
        return this.fly_ash_sample;
    }
    
    /**
     * Setter for property fly_ash_sample.
     * @param flyash New value of property fly_ash_sample.
     */
    public void setFly_ash_sample(String fly_ash_sample)   {
        
        this.fly_ash_sample = fly_ash_sample;
    }
    
    /**
     * Getter for property slag_sample.
     * @return Value of property slag_sample.
     */
    public String getSlag_sample()  {
        
        return this.slag_sample;
    }
    
    /**
     * Setter for property slag_sample.
     * @param slag New value of property slag_sample.
     */
    public void setSlag_sample(String slag_sample)  {
        
        this.slag_sample = slag_sample;
    }
    
    /**
     * Getter for property caco3_sample.
     * @return Value of property caco3_sample.
     */
    public String getCaco3_sample()  {
        
        return this.caco3_sample;
    }
    
    /**
     * Setter for property caco3_sample.
     * @param caco3 New value of property caco3_sample.
     */
    public void setCaco3_sample(String caco3_sample)  {
        
        this.caco3_sample = caco3_sample;
    }
    
    /**
     * Getter for property free_lime_sample.
     * @return Value of property free_lime_sample.
     */
    public String getFree_lime_sample()   {
        
        return this.free_lime_sample;
    }
    
    /**
     * Setter for property free_lime_sample.
     * @param freelime New value of property free_lime_sample.
     */
    public void setFree_lime_sample(String free_lime_sample)   {
        
        this.free_lime_sample = free_lime_sample;
    }
    
    /**
     * Getter for property inert_filler_sample.
     * @return Value of property inert_filler_sample.
     */
    public String getInert_filler_sample()   {
        
        return this.inert_filler_sample;
    }
    
    /**
     * Setter for property inert_filler_sample.
     * @param inertfiller New value of property inert_filler_sample.
     */
    public void setInert_filler_sample(String inert_filler_sample)   {
        
        this.inert_filler_sample = inert_filler_sample;
    }
    
    /**
     * Getter for property dihydrate_sample.
     * @return Value of property dihydrate_sample.
     */
    public String getDihydrate_sample()  {
        
        return this.dihydrate_sample;
    }
    
    /**
     * Setter for property dihydrate_sample.
     * @param dihydrate New value of property dihydrate_sample.
     */
    public void setDihydrate_sample(String dihydrate_sample)  {
        
        this.dihydrate_sample = dihydrate_sample;
    }
    
    /**
     * Getter for property anhydrite_sample.
     * @return Value of property anhydrite_sample.
     */
    public String getAnhydrite_sample()   {
        
        return this.anhydrite_sample;
    }
    
    /**
     * Setter for property anhydrite_sample.
     * @param anhydrite New value of property anhydrite_sample.
     */
    public void setAnhydrite_sample(String anhydrite_sample)   {
        
        this.anhydrite_sample = anhydrite_sample;
    }
    
    /**
     * Getter for property hemihydrate_sample.
     * @return Value of property hemihydrate_sample.
     */
    public String getHemihydrate_sample()  {
        
        return this.hemihydrate_sample;
    }
    
    /**
     * Setter for property hemihydrate_sample.
     * @param hemihydrate New value of property hemihydrate_sample.
     */
    public void setHemihydrate_sample(String hemihydrate_sample)  {
        
        this.hemihydrate_sample = hemihydrate_sample;
    }
    
    /**
     * Holds value of property c3s_vf.
     */
    private String c3s_vf;
    
    /**
     * Holds value of property c3s_saf.
     */
    private String c3s_saf;
    
    /**
     * Holds value of property c2s_vf.
     */
    private String c2s_vf;
    
    /**
     * Holds value of property c2s_saf.
     */
    private String c2s_saf;
    
    /**
     * Holds value of property c3a_vf.
     */
    private String c3a_vf;
    
    /**
     * Holds value of property c3a_saf.
     */
    private String c3a_saf;
    
    /**
     * Holds value of property c4af_vf.
     */
    private String c4af_vf;
    
    /**
     * Holds value of property c4af_saf.
     */
    private String c4af_saf;
    
    /**
     * Holds value of property k2so4_vf.
     */
    private String k2so4_vf;
    
    /**
     * Holds value of property k2so4_saf.
     */
    private String k2so4_saf;
    
    /**
     * Holds value of property na2so4_vf.
     */
    private String na2so4_vf;
    
    /**
     * Holds value of property na2so4_saf.
     */
    private String na2so4_saf;
    
    /**
     * Holds value of property k2so4_corr.
     */
    private boolean k2so4_corr;
    
    /**
     * Holds value of property na2so4_corr.
     */
    private boolean na2so4_corr;
    
    /**
     * Holds value of property sum_vf.
     */
    private String sum_vf;
    
    /**
     * Holds value of property sum_saf.
     */
    private String sum_saf;
    
    /**
     * Holds value of property clinker_action.
     */
    private String clinker_action;
    
    
    public void updateFractions() throws SQLArgumentException, SQLException, ParseException {
        // String psd = getPsd_selected();
        if (cementName.equalsIgnoreCase("")) {
            return;
        }
        String pfc;
        pfc = CementDatabase.getPfc(cementName);
        String[] fracs = pfc.split("\n");
        
        String[] c3sf = getFracs(fracs[0]);
        this.setC3s_vf(c3sf[0]);
        this.setC3s_saf(c3sf[1]);
        
        String[] c2sf = getFracs(fracs[1]);
        this.setC2s_vf(c2sf[0]);
        this.setC2s_saf(c2sf[1]);
        
        String[] c3af = getFracs(fracs[2]);
        this.setC3a_vf(c3af[0]);
        this.setC3a_saf(c3af[1]);
        
        String[] c4aff = getFracs(fracs[3]);
        this.setC4af_vf(c4aff[0]);
        this.setC4af_saf(c4aff[1]);
        
        // Check if K2SO4 and Na2SO4 correlation files are in database
        String k2so4Corr = CementDatabase.getK2o(cementName);
        String na2so4Corr = CementDatabase.getN2o(cementName);
        
        boolean use_k2so4 = (k2so4Corr != null);
        boolean use_na2so4 = (na2so4Corr != null);
        if (use_k2so4 && (fracs.length > 4)) {
            String[] k2so4f = getFracs(fracs[4]);
            this.setK2so4_vf(k2so4f[0]);
            this.setK2so4_saf(k2so4f[1]);
        } else {
            this.setK2so4_vf("0.0000");
            this.setK2so4_saf("0.0000");
        }
        
        if (use_na2so4 && (fracs.length > 5)) {
            String[] na2so4f = getFracs(fracs[5]);
            this.setNa2so4_vf(na2so4f[0]);
            this.setNa2so4_saf(na2so4f[1]);
        } else {
            this.setNa2so4_vf("0.0000");
            this.setNa2so4_saf("0.0000");
        }
        
        this.setK2so4_corr(use_k2so4);
        this.setNa2so4_corr(use_na2so4);
        
        sum_fractions();
    }
    
    private void sum_fractions() throws ParseException {
        try {
            double sumVolumeFractions = 0.0;
            double sumSurfaceAreaFraction = 0.0;
            double nsumVolumeFractions = 0.0;
            double nsumSurfaceAreaFraction = 0.0;
            
            sumVolumeFractions += Double.parseDouble(this.getC3s_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getC3s_saf());
            
            sumVolumeFractions += Double.parseDouble(this.getC2s_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getC2s_saf());
            
            sumVolumeFractions += Double.parseDouble(this.getC3a_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getC3a_saf());
            
            sumVolumeFractions += Double.parseDouble(this.getC4af_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getC4af_saf());
            
            sumVolumeFractions += Double.parseDouble(this.getK2so4_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getK2so4_saf());
            
            sumVolumeFractions += Double.parseDouble(this.getNa2so4_vf());
            sumSurfaceAreaFraction += Double.parseDouble(this.getNa2so4_saf());
            
            DecimalFormatSymbols decFormSymb = new DecimalFormatSymbols();
            decFormSymb.setDecimalSeparator('.');
            NumberFormat frac_format = new DecimalFormat("0.000", decFormSymb);
          
            this.setSum_vf(frac_format.format(sumVolumeFractions));
            this.setSum_saf(frac_format.format(sumSurfaceAreaFraction));
            
           // this.setSum_vf(Double.toString(sumVolumeFractions));
           // this.setSum_saf(Double.toString(sumSurfaceAreaFraction));

        } catch (NumberFormatException nfe) {
            
        }
    }
    
    static private String[] getFracs(String fracpair) {
        fracpair = fracpair.trim();
        // Delimiter may be a tab or space
        int endfirst = fracpair.indexOf('\t');
        if (endfirst < 0) {
            endfirst = fracpair.indexOf(' ');
        }
        String[] result = new String[2];
        result[0] = fracpair.substring(0, endfirst).trim();
        result[1] = fracpair.substring(endfirst).trim();
        
        return result;
    }
    
    /**
     * Getter for property c3svf.
     * @return Value of property c3svf.
     */
    public String getC3s_vf()  {
        
        return this.c3s_vf;
    }
    
    /**
     * Setter for property c3svf.
     * @param c3svf New value of property c3svf.
     */
    public void setC3s_vf(String c3s_vf)  {
        
        this.c3s_vf = c3s_vf;
    }
    
    /**
     * Getter for property c3s_saf.
     * @return Value of property c3s_saf.
     */
    public String getC3s_saf() {
        
        return this.c3s_saf;
    }
    
    /**
     * Setter for property c3s_saf.
     * @param c3s_saf New value of property c3s_saf.
     */
    public void setC3s_saf(String c3s_saf) {
        
        this.c3s_saf = c3s_saf;
    }
    
    /**
     * Getter for property c2s_vf.
     * @return Value of property c2s_vf.
     */
    public String getC2s_vf() {
        
        return this.c2s_vf;
    }
    
    /**
     * Setter for property c2s_vf.
     * @param c2s_vf New value of property c2s_vf.
     */
    public void setC2s_vf(String c2s_vf) {
        
        this.c2s_vf = c2s_vf;
    }
    
    /**
     * Getter for property c2s_saf.
     * @return Value of property c2s_saf.
     */
    public String getC2s_saf() {
        
        return this.c2s_saf;
    }
    
    /**
     * Setter for property c2s_saf.
     * @param c2s_saf New value of property c2s_saf.
     */
    public void setC2s_saf(String c2s_saf) {
        
        this.c2s_saf = c2s_saf;
    }
    
    /**
     * Getter for property c3a_vf.
     * @return Value of property c3a_vf.
     */
    public String getC3a_vf() {
        
        return this.c3a_vf;
    }
    
    /**
     * Setter for property c3a_vf.
     * @param c3a_vf New value of property c3a_vf.
     */
    public void setC3a_vf(String c3a_vf) {
        
        this.c3a_vf = c3a_vf;
    }
    
    /**
     * Getter for property c3a_saf.
     * @return Value of property c3a_saf.
     */
    public String getC3a_saf() {
        
        return this.c3a_saf;
    }
    
    /**
     * Setter for property c3a_saf.
     * @param c3a_saf New value of property c3a_saf.
     */
    public void setC3a_saf(String c3a_saf) {
        
        this.c3a_saf = c3a_saf;
    }
    
    /**
     * Getter for property c4af_vf.
     * @return Value of property c4af_vf.
     */
    public String getC4af_vf() {
        
        return this.c4af_vf;
    }
    
    /**
     * Setter for property c4af_vf.
     * @param c4af_vf New value of property c4af_vf.
     */
    public void setC4af_vf(String c4af_vf) {
        
        this.c4af_vf = c4af_vf;
    }
    
    /**
     * Getter for property c4af_saf.
     * @return Value of property c4af_saf.
     */
    public String getC4af_saf() {
        
        return this.c4af_saf;
    }
    
    /**
     * Setter for property c4af_saf.
     * @param c4af_saf New value of property c4af_saf.
     */
    public void setC4af_saf(String c4af_saf) {
        
        this.c4af_saf = c4af_saf;
    }
    
    /**
     * Getter for property k2so4_vf.
     * @return Value of property k2so4_vf.
     */
    public String getK2so4_vf() {
        
        return this.k2so4_vf;
    }
    
    /**
     * Setter for property k2so4_vf.
     * @param k2so4_vf New value of property k2so4_vf.
     */
    public void setK2so4_vf(String k2so4_vf) {
        
        this.k2so4_vf = k2so4_vf;
    }
    
    /**
     * Getter for property k2so4_saf.
     * @return Value of property k2so4_saf.
     */
    public String getK2so4_saf() {
        
        return this.k2so4_saf;
    }
    
    /**
     * Setter for property k2so4_saf.
     * @param k2so4_saf New value of property k2so4_saf.
     */
    public void setK2so4_saf(String k2so4_saf) {
        
        this.k2so4_saf = k2so4_saf;
    }
    
    /**
     * Getter for property na2so4_vf.
     * @return Value of property na2so4_vf.
     */
    public String getNa2so4_vf() {
        
        return this.na2so4_vf;
    }
    
    /**
     * Setter for property na2so4_vf.
     * @param na2so4_vf New value of property na2so4_vf.
     */
    public void setNa2so4_vf(String na2so4_vf) {
        
        this.na2so4_vf = na2so4_vf;
    }
    
    /**
     * Getter for property na2so4_saf.
     * @return Value of property na2so4_saf.
     */
    public String getNa2so4_saf() {
        
        return this.na2so4_saf;
    }
    
    /**
     * Setter for property na2so4_saf.
     * @param na2so4_saf New value of property na2so4_saf.
     */
    public void setNa2so4_saf(String na2so4_saf) {
        
        this.na2so4_saf = na2so4_saf;
    }
    
    /**
     * Getter for property k2so4_corr.
     * @return Value of property k2so4_corr.
     */
    public boolean isK2so4_corr() {
        
        return this.k2so4_corr;
    }
    
    /**
     * Setter for property k2so4_corr.
     * @param k2so4_corr New value of property k2so4_corr.
     */
    public void setK2so4_corr(boolean k2so4_corr) {
        
        this.k2so4_corr = k2so4_corr;
    }
    
    /**
     * Getter for property na2so4_corr.
     * @return Value of property na2so4_corr.
     */
    public boolean isNa2so4_corr() {
        
        return this.na2so4_corr;
    }
    
    /**
     * Setter for property na2so4_corr.
     * @param na2so4_corr New value of property na2so4_corr.
     */
    public void setNa2so4_corr(boolean na2so4_corr) {
        
        this.na2so4_corr = na2so4_corr;
    }
    
    /**
     * Getter for property sum_vf.
     * @return Value of property sum_vf.
     */
    public String getSum_vf() {
        
        return this.sum_vf;
    }
    
    /**
     * Setter for property sum_vf.
     * @param sum_vf New value of property sum_vf.
     */
    public void setSum_vf(String sum_vf) {
        
        this.sum_vf = sum_vf;
    }
    
    /**
     * Getter for property sum_saf.
     * @return Value of property sum_saf.
     */
    public String getSum_saf() {
        
        return this.sum_saf;
    }
    
    /**
     * Setter for property sum_saf.
     * @param sum_saf New value of property sum_saf.
     */
    public void setSum_saf(String sum_saf) {
        
        this.sum_saf = sum_saf;
    }
    
    /**
     * Getter for property clinker_action.
     * @return Value of property clinker_action.
     */
    public String getClinker_action() {
        
        return this.clinker_action;
    }
    
    /**
     * Setter for property clinker_action.
     * @param clinker_action New value of property clinker_action.
     */
    public void setClinker_action(String clinker_action) {
        
        this.clinker_action = clinker_action;
    }
    
    public void updateSulfateFractionsGivenCement(String cement) throws SQLArgumentException, SQLException, ParseException {
        String psd = CementDatabase.getCementPSD(cement);
        this.setDihydrate_psd(psd);
        this.setHemihydrate_psd(psd);
        this.setAnhydrite_psd(psd);
        
        this.updateSulfateMassFractionsGivenCement(cement);
        this.updateSulfateVolumeFractionsGivenCement(cement);
        
        //calculateVolumeFractionsGivenMassFractions();
    }
    
    public void updateSulfateVolumeFractionsGivenCement(String cement) throws ParseException {
        double massFrac;
        
        double cementSpecificGravity = this.calculateCementSpecificGravity();
        massFrac = Double.parseDouble(this.getDihydrate_massfrac());
        this.setDihydrate_volfrac(Double.toString(Util.round(massFrac*cementSpecificGravity/Constants.DIHYDRATE_SPECIFIC_GRAVITY,4)));
        massFrac = Double.parseDouble(this.getHemihydrate_massfrac());
        this.setHemihydrate_volfrac(Double.toString(Util.round(massFrac*cementSpecificGravity/Constants.HEMIHYDRATE_SPECIFIC_GRAVITY,4)));
        massFrac = Double.parseDouble(this.getAnhydrite_massfrac());
        this.setAnhydrite_volfrac(Double.toString(Util.round(massFrac*cementSpecificGravity/Constants.ANHYDRITE_SPECIFIC_GRAVITY,4)));
    }
    
    public void updateSulfateMassFractionsGivenCement(String cement) throws SQLArgumentException, SQLException {
        // NumberFormat ffmt = new DecimalFormat("0.000000000");
        double[] sulf = CementDatabase.getSulfateFractions(cement);
        
        this.setDihydrate_massfrac(Double.toString(Util.round(sulf[0],4)));
        this.setHemihydrate_massfrac(Double.toString(Util.round(sulf[1],4)));
        this.setAnhydrite_massfrac(Double.toString(Util.round(sulf[2],4)));
    }
    
    // For use in Blend (i.e., FractionsAndPSD) page
    public void calculateVolumeFractionsGivenMassFractions() throws ParseException {
        double sumMass = 0.0;
        double sumVolume = 0.0;
        double mass;
        
        // Cement
        mass = Double.parseDouble(this.getCement_massfrac());
        double cementSpecificGravity = this.calculateCementSpecificGravity();
        double cementVolume = mass/cementSpecificGravity;
        // cementVolume = stringToDouble(this.getCement_volfrac());
        sumMass += mass;
        sumVolume += cementVolume;
        // Silica fume
        mass = Double.parseDouble(this.getSilica_fume_massfrac());
        double silicaFumeVolume = mass/Constants.SILICA_FUME_SPECIFIC_GRAVITY;
        sumMass += mass;
        sumVolume += silicaFumeVolume;
        // Fly ash
        mass = Double.parseDouble(this.getFly_ash_massfrac());
        // String fname = this.getFly_ash_psd();
        // double flyAshSpecificGravity = FlyAsh.get_specific_gravity(fname);
        double flyAshSpecificGravity = Double.parseDouble(this.getFly_ash_sg());
        double flyAshVolume = mass/flyAshSpecificGravity;
        sumMass += mass;
        sumVolume += flyAshVolume;
        // Slag
        mass = Double.parseDouble(this.getSlag_massfrac());
        // fname = this.getSlag_psd();
        // double slagAshSpecificFravity = Slag.get_specific_gravity(fname);
        double slagAshSpecificFravity = Double.parseDouble(this.getSlag_sg());
        double slagAshVolume = mass/slagAshSpecificFravity;
        sumMass += mass;
        sumVolume += slagAshVolume;
        // Caco3
        mass = Double.parseDouble(this.getCaco3_massfrac());
        double caco3Volume = mass/Constants.CACO3_SPECIFIC_GRAVITY;
        sumMass += mass;
        sumVolume += caco3Volume;
        // Free Lime
        mass = Double.parseDouble(this.getFree_lime_massfrac());
        double FreeLimeVolume = mass/Constants.FREE_LIME_SPECIFIC_GRAVITY;
        sumMass += mass;
        sumVolume += FreeLimeVolume;
        // Inert Filler
        mass = Double.parseDouble(this.getInert_filler_massfrac());
        // fname = this.getInert_filler_psd();
        // double inertFillerSpecificGravity = InertFiller.get_specific_gravity(fname);
        double inertFillerSpecificGravity = Double.parseDouble(this.getInert_filler_sg());
        double inertFillerVolume = mass/inertFillerSpecificGravity;
        sumMass += mass;
        sumVolume += inertFillerVolume;
        
        // Now set all the volume fractions
        this.setCement_volfrac(Double.toString(Util.round(cementVolume/sumVolume,4)));
        this.setSilica_fume_volfrac(Double.toString(Util.round(silicaFumeVolume/sumVolume,4)));
        this.setFly_ash_volfrac(Double.toString(Util.round(flyAshVolume/sumVolume,4)));
        this.setSlag_volfrac(Double.toString(Util.round(slagAshVolume/sumVolume,4)));
        this.setCaco3_volfrac(Double.toString(Util.round(caco3Volume/sumVolume,4)));
        this.setFree_lime_volfrac(Double.toString(Util.round(FreeLimeVolume/sumVolume,4)));
        this.setInert_filler_volfrac(Double.toString(Util.round(inertFillerVolume/sumVolume,4)));
        
        // Binder, coarse aggregate, fine aggregate and water
        this.updateBinderSpecificGravity();
        sumMass = 0.0;
        sumVolume = 0.0;
        
        // Binder
        mass = Double.parseDouble(this.getBinder_massfrac());
        double binderSpecificGravity = Double.parseDouble(this.getBinder_sg());
        double binderVolume = mass/binderSpecificGravity;
        sumMass += mass;
        sumVolume += binderVolume;
        // Coarse aggregate 01
        mass = Double.parseDouble(this.getCoarse_aggregate01_massfrac());
        double coarseAggregate01SpecificGravity = Double.parseDouble(this.getCoarse_aggregate01_sg());
        double coarseAggregate01Volume = mass/coarseAggregate01SpecificGravity;
        sumMass += mass;
        sumVolume += coarseAggregate01Volume;
        // Fine aggregate 01
        mass = Double.parseDouble(this.getFine_aggregate01_massfrac());
        double fineAggregate01SpecificGravity = Double.parseDouble(this.getFine_aggregate01_sg());
        double fineAggregate01Volume = mass/fineAggregate01SpecificGravity;
        sumMass += mass;
        sumVolume += fineAggregate01Volume;

        // Coarse aggregate 01
        mass = Double.parseDouble(this.getCoarse_aggregate01_massfrac());
        double coarseAggregate02SpecificGravity = Double.parseDouble(this.getCoarse_aggregate02_sg());
        double coarseAggregate02Volume = mass/coarseAggregate02SpecificGravity;
        sumMass += mass;
        sumVolume += coarseAggregate02Volume;
        // Fine aggregate 02
        mass = Double.parseDouble(this.getFine_aggregate02_massfrac());
        double fineAggregate02SpecificGravity = Double.parseDouble(this.getFine_aggregate02_sg());
        double fineAggregate02Volume = mass/fineAggregate02SpecificGravity;
        sumMass += mass;
        sumVolume += fineAggregate02Volume;

        double solidMass = sumMass;
        
        // Water
        mass = Double.parseDouble(this.getWater_massfrac());
        double waterVolume = mass/Constants.WATER_DENSITY;
        sumVolume += waterVolume;
        sumMass += mass;
        
        // Set water/solid ratio
        this.setWater_binder_ratio(Double.toString(Util.round(mass/solidMass,3)));
        
        // Now set all the volume fractions
        this.setBinder_volfrac(Double.toString(Util.round(binderVolume/sumVolume,4)));
        this.setCoarse_aggregate01_volfrac(Double.toString(Util.round(coarseAggregate01Volume/sumVolume,4)));
        this.setFine_aggregate01_volfrac(Double.toString(Util.round(fineAggregate01Volume/sumVolume,4)));
        this.setCoarse_aggregate02_volfrac(Double.toString(Util.round(coarseAggregate02Volume/sumVolume,4)));
        this.setFine_aggregate02_volfrac(Double.toString(Util.round(fineAggregate02Volume/sumVolume,4)));

        this.setWater_volfrac(Double.toString(Util.round(waterVolume/sumVolume,4)));
    }
    
    public void updateFlyAshSpecificGravity() throws SQLException, SQLArgumentException, DBFileException {
        double sg = FlyAsh.get_specific_gravity(this.getFly_ash_psd());
        // NumberFormat ffmt = new DecimalFormat("0.000000000");
        this.setFly_ash_sg(Double.toString(Util.round(sg,4)));
    }
    
    public void updateSlagSpecificGravity() throws SQLException, SQLArgumentException, DBFileException {
        double sg = Slag.get_specific_gravity(this.getSlag_psd());
        // NumberFormat ffmt = new DecimalFormat("0.000000000");
        this.setSlag_sg(Double.toString(Util.round(sg,4)));
    }
    
    public void updateInertFillerSpecificGravity() throws SQLException, SQLArgumentException, DBFileException {
        double sg = InertFiller.get_specific_gravity(this.getInert_filler_psd());
        // NumberFormat ffmt = new DecimalFormat("0.000000000");
        this.setInert_filler_sg(Double.toString(Util.round(sg,4)));
    }
    
    private void updateBinderSpecificGravity() throws ParseException {
        // Verify that it's correct
        double cementMassFrac = Double.parseDouble(this.getCement_massfrac());
        double cementVolumeFrac = Double.parseDouble(this.getCement_volfrac());
        double cementSpecificGravity = this.calculateCementSpecificGravity();
        double binderSpecificGravity = (cementVolumeFrac/cementMassFrac)*cementSpecificGravity;
        this.setBinder_sg(Double.toString(Util.round(binderSpecificGravity,4)));
    }
    
    public double calculateCementSpecificGravity() throws ParseException {
        double totalVolume = 0;
        double clinkerMassFraction; // mass fraction of CLINKER in CEMENT (not just clinker. cement = clinker + calcium sulfates)
        double clinkerSpecificGravity = 0;
        
        // this.updateSulfateMassFractionsGivenCement();
        
        /**
         * Calculate mass fraction of clinker in cement
         **/
        double dihydrateMassFraction = Double.parseDouble(this.getDihydrate_massfrac());
        double hemihydrateMassFraction = Double.parseDouble(this.getHemihydrate_massfrac());
        double anhydriteMassFraction = Double.parseDouble(this.getAnhydrite_massfrac());
        clinkerMassFraction = 1 - dihydrateMassFraction - hemihydrateMassFraction - anhydriteMassFraction;
        
        /**
         * Normalize volume fractions in CLINKER
         **/
        double c3sVolumeFraction = Double.parseDouble(this.getC3s_vf()); // volume fraction in CLINKER
        totalVolume += c3sVolumeFraction;
        
        double c2sVolumeFraction = Double.parseDouble(this.getC2s_vf()); // volume fraction in CLINKER
        totalVolume += c2sVolumeFraction;
        
        double c3aVolumeFraction = Double.parseDouble(this.getC3a_vf()); // volume fraction in CLINKER
        totalVolume += c3aVolumeFraction;
        
        double c4afVolumeFraction = Double.parseDouble(this.getC4af_vf()); // volume fraction in CLINKER
        totalVolume += c4afVolumeFraction;
        
        double k2so4VolumeFraction = Double.parseDouble(this.getK2so4_vf()); // volume fraction in CLINKER
        totalVolume += k2so4VolumeFraction;
        
        double na2so4VolumeFraction = Double.parseDouble(this.getNa2so4_vf()); // volume fraction in CLINKER
        totalVolume += na2so4VolumeFraction;
        
        c3sVolumeFraction /= totalVolume;
        clinkerSpecificGravity += c3sVolumeFraction * Constants.C3S_SPECIFIC_GRAVITY;
        
        c2sVolumeFraction /= totalVolume;
        clinkerSpecificGravity += c2sVolumeFraction * Constants.C2S_SPECIFIC_GRAVITY;
        
        c3aVolumeFraction /= totalVolume;
        clinkerSpecificGravity += c3aVolumeFraction * Constants.C3A_SPECIFIC_GRAVITY;
        
        c4afVolumeFraction /= totalVolume;
        clinkerSpecificGravity += c4afVolumeFraction * Constants.C4AF_SPECIFIC_GRAVITY;
        
        k2so4VolumeFraction /= totalVolume;
        clinkerSpecificGravity += k2so4VolumeFraction * Constants.K2SO4_SPECIFIC_GRAVITY;
        
        na2so4VolumeFraction /= totalVolume;
        clinkerSpecificGravity += na2so4VolumeFraction * Constants.NA2SO4_SPECIFIC_GRAVITY;
        
        /**
         * Calculate total volume in 1g of CEMENT
         **/
        totalVolume = 0;
        totalVolume += c3sVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += c2sVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += c3aVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += c4afVolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += k2so4VolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += na2so4VolumeFraction * clinkerMassFraction / clinkerSpecificGravity;
        totalVolume += dihydrateMassFraction / Constants.DIHYDRATE_SPECIFIC_GRAVITY;
        totalVolume += hemihydrateMassFraction / Constants.HEMIHYDRATE_SPECIFIC_GRAVITY;
        totalVolume += anhydriteMassFraction / Constants.ANHYDRITE_SPECIFIC_GRAVITY;
        
        return 1 / totalVolume; // mass = 1
    }
    
    /**
     * Holds value of property fly_ash_sg.
     */
    private String fly_ash_sg;
    
    /**
     * Getter for property flyash_sg.
     * @return Value of property flyash_sg.
     */
    public String getFly_ash_sg() {
        
        return this.fly_ash_sg;
    }
    
    /**
     * Setter for property flyash_sg.
     * @param flyash_sg New value of property flyash_sg.
     */
    public void setFly_ash_sg(String fly_ash_sg) {
        
        this.fly_ash_sg = fly_ash_sg;
    }
    
    /**
     * Holds value of property slag_sg.
     */
    private String slag_sg;
    
    /**
     * Getter for property slag_sg.
     * @return Value of property slag_sg.
     */
    public String getSlag_sg() {
        
        return this.slag_sg;
    }
    
    /**
     * Setter for property slag_sg.
     * @param slag_sg New value of property slag_sg.
     */
    public void setSlag_sg(String slag_sg) {
        
        this.slag_sg = slag_sg;
    }
    
    /**
     * Holds value of property inert_filler_sg.
     */
    private String inert_filler_sg;
    
    /**
     * Getter for property inert_filler_sg.
     * @return Value of property inert_filler_sg.
     */
    public String getInert_filler_sg() {
        
        return this.inert_filler_sg;
    }
    
    /**
     * Setter for property inert_filler_sg.
     * @param inert_filler_sg New value of property inert_filler_sg.
     */
    public void setInert_filler_sg(String inert_filler_sg) {
        
        this.inert_filler_sg = inert_filler_sg;
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
     * Holds value of property fine_aggregate01_sg.
     */
    private String fine_aggregate01_sg;
    
    /**
     * Getter for property fine_aggregate01_specific_gravity.
     * @return Value of property fine_aggregate01_specific_gravity.
     */
    public String getFine_aggregate01_sg() {
        return this.fine_aggregate01_sg;
    }
    
    /**
     * Setter for property fine_aggregate01_specific_gravity.
     * @param fine_aggregate01_specific_gravity New value of property fine_aggregate01_specific_gravity.
     */
    public void setFine_aggregate01_sg(String fine_aggregate01_sg) {
        this.fine_aggregate01_sg = fine_aggregate01_sg;
    }
    
    /**
     * Holds value of property coarse_aggregate01_sg.
     */
    private String coarse_aggregate01_sg;
    
    /**
     * Getter for property coarse_aggregate01_specific_gravity.
     * @return Value of property coarse_aggregate01_specific_gravity.
     */
    public String getCoarse_aggregate01_sg() {
        return this.coarse_aggregate01_sg;
    }
    
    /**
     * Setter for property coarse_aggregate01_specific_gravity.
     * @param coarse_aggregate01_specific_gravity New value of property coarse_aggregate01_specific_gravity.
     */
    public void setCoarse_aggregate01_sg(String coarse_aggregate01_sg) {
        this.coarse_aggregate01_sg = coarse_aggregate01_sg;
    }
    
    /**
     * Holds value of property fine_aggregate01_grading_name.
     */
    private String fine_aggregate01_grading_name;
    
    /**
     * Getter for property fine_aggregate01_grading.
     * @return Value of property fine_aggregate01_grading.
     */
    public String getFine_aggregate01_grading_name() {
        return this.fine_aggregate01_grading_name;
    }
    
    /**
     * Setter for property fine_aggregate01_grading.
     * @param fine_aggregate01_grading New value of property fine_aggregate01_grading.
     */
    public void setFine_aggregate01_grading_name(String fine_aggregate01_grading_name) {
        this.previousFine01Grading = this.fine_aggregate01_grading_name;
        this.fine_aggregate01_grading_name = fine_aggregate01_grading_name;
    }
    
    /**
     * Holds value of property coarse_aggregate01_grading_name.
     */
    private String coarse_aggregate01_grading_name;
    
    /**
     * Getter for property coarse_aggregate01_grading.
     * @return Value of property coarse_aggregate01_grading.
     */
    public String getCoarse_aggregate01_grading_name() {
        return this.coarse_aggregate01_grading_name;
    }
    
    /**
     * Setter for property coarse_aggregate01_grading.
     * @param coarse_aggregate01_grading New value of property coarse_aggregate01_grading.
     */
    public void setCoarse_aggregate01_grading_name(String coarse_aggregate01_grading_name) {
        this.previousCoarse01Grading = this.coarse_aggregate01_grading_name;
        this.coarse_aggregate01_grading_name = coarse_aggregate01_grading_name;
    }

     /**
     * Holds value of property fine_aggregate02_sg.
     */
    private String fine_aggregate02_sg;

    /**
     * Getter for property fine_aggregate02_specific_gravity.
     * @return Value of property fine_aggregate02_specific_gravity.
     */
    public String getFine_aggregate02_sg() {
        return this.fine_aggregate02_sg;
    }

    /**
     * Setter for property fine_aggregate02_specific_gravity.
     * @param fine_aggregate02_specific_gravity New value of property fine_aggregate02_specific_gravity.
     */
    public void setFine_aggregate02_sg(String fine_aggregate02_sg) {
        this.fine_aggregate02_sg = fine_aggregate02_sg;
    }

    /**
     * Holds value of property coarse_aggregate02_sg.
     */
    private String coarse_aggregate02_sg;

    /**
     * Getter for property coarse_aggregate02_specific_gravity.
     * @return Value of property coarse_aggregate02_specific_gravity.
     */
    public String getCoarse_aggregate02_sg() {
        return this.coarse_aggregate02_sg;
    }

    /**
     * Setter for property coarse_aggregate02_specific_gravity.
     * @param coarse_aggregate02_specific_gravity New value of property coarse_aggregate02_specific_gravity.
     */
    public void setCoarse_aggregate02_sg(String coarse_aggregate02_sg) {
        this.coarse_aggregate02_sg = coarse_aggregate02_sg;
    }

    /**
     * Holds value of property fine_aggregate02_grading_name.
     */
    private String fine_aggregate02_grading_name;

    /**
     * Getter for property fine_aggregate01_grading.
     * @return Value of property fine_aggregate01_grading.
     */
    public String getFine_aggregate02_grading_name() {
        return this.fine_aggregate02_grading_name;
    }

    /**
     * Setter for property fine_aggregate02_grading.
     * @param fine_aggregate02_grading New value of property fine_aggregate02_grading.
     */
    public void setFine_aggregate02_grading_name(String fine_aggregate02_grading_name) {
        this.previousFine02Grading = this.fine_aggregate02_grading_name;
        this.fine_aggregate02_grading_name = fine_aggregate02_grading_name;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_name.
     */
    private String coarse_aggregate02_grading_name;

    /**
     * Getter for property coarse_aggregate02_grading.
     * @return Value of property coarse_aggregate02_grading.
     */
    public String getCoarse_aggregate02_grading_name() {
        return this.coarse_aggregate02_grading_name;
    }

    /**
     * Setter for property coarse_aggregate02_grading.
     * @param coarse_aggregate02_grading New value of property coarse_aggregate02_grading.
     */
    public void setCoarse_aggregate02_grading_name(String coarse_aggregate02_grading_name) {
        this.previousCoarse02Grading = this.coarse_aggregate02_grading_name;
        this.coarse_aggregate02_grading_name = coarse_aggregate02_grading_name;
    }

    /**
     * Get the data grading whose name is gradingName
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @param gradingName Name of the desired grading.
     * @return Data grading
     **/
    static public String[][] getGradingFromDatabase(String gradingName) throws SQLArgumentException, SQLException {
        String grading = CementDatabase.getGrading(gradingName);
        return getGradingFromString(grading);
    }
    
    static public String[][] getGradingFromString(String grading) {
        String[] lines = grading.split("\n");
        
        int firstUsefullLine = 0;
        if (lines[0].startsWith("Sieve"))
            firstUsefullLine++;
        String parts[];
        String[][] result = new String[3][lines.length-firstUsefullLine];
        for (int i = firstUsefullLine; i < lines.length; i++) {
            parts = lines[i].split("\t");
            result[0][i-firstUsefullLine] = parts[0];
            result[1][i-firstUsefullLine] = parts[1];
            result[2][i-firstUsefullLine] = parts[2];
        }
        return result;
    }
    
    /**
     * Get the data grading of the fine aggregate 01
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getFine01GradingFromDatabase() throws SQLArgumentException, SQLException {
        return getGradingFromDatabase(fine_aggregate01_grading_name);
    }
    
    /**
     * Get the data grading of the coarse aggregate 01
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getCoarse01GradingFromDatabase() throws SQLArgumentException, SQLException {
        return getGradingFromDatabase(coarse_aggregate01_grading_name);
    }
    
    /**
     * Get the data grading of the fine aggregate 01
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getFine01Grading() {
        return getGradingFromString(fine_aggregate01_grading);
    }
    
    /**
     * Get the data grading of the coarse aggregate 01
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getCoarse01Grading() {
        return getGradingFromString(coarse_aggregate01_grading);
    }
    
    /**
     * Holds value of property fine_aggregate01_grading_max_diam.
     */
    private String fine_aggregate01_grading_max_diam;
    
    /**
     * Getter for property fine_aggregate01_grading_max_diam.
     * @return Value of property fine_aggregate01_grading_max_diam.
     */
    public String getFine_aggregate01_grading_max_diam() {
        return this.fine_aggregate01_grading_max_diam;
    }
    
    /**
     * Setter for property fine_aggregate01_grading_max_diam.
     * @param fine_aggregate_grading01_max_diam New value of property fine_aggregate01_grading_max_diam.
     */
    public void setFine_aggregate01_grading_max_diam(String fine_aggregate01_grading_max_diam) {
        this.fine_aggregate01_grading_max_diam = fine_aggregate01_grading_max_diam;
    }
    
    /**
     * Holds value of property coarse_aggregate01_grading_max_diam.
     */
    private String coarse_aggregate01_grading_max_diam;
    
    /**
     * Getter for property coarse_aggregate01_grading_max_diam.
     * @return Value of property coarse_aggregate01_grading_max_diam.
     */
    public String getCoarse_aggregate01_grading_max_diam() {
        return this.coarse_aggregate01_grading_max_diam;
    }
    
    /**
     * Setter for property coarse_aggregate01_grading_max_diam.
     * @param coarse_aggregate01_grading_max_diam New value of property coarse_aggregate01_grading_max_diam.
     */
    public void setCoarse_aggregate01_grading_max_diam(String coarse_aggregate01_grading_max_diam) {
        this.coarse_aggregate01_grading_max_diam = coarse_aggregate01_grading_max_diam;
    }

     /**
     * Holds value of property coarse_aggregate01_grading_massfrac_0.
     */
    private String coarse_aggregate01_grading_massfrac_0;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_0.
     * @return Value of property coarse_aggregate01_grading_massfrac_0.
     */
    public String getCoarse_aggregate01_grading_massfrac_0() {
        return this.coarse_aggregate01_grading_massfrac_0;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_0.
     * @param coarse_aggregate01_grading_massfrac_0 New value of property coarse_aggregate01_grading_massfrac_0.
     */
    public void setCoarse_aggregate01_grading_massfrac_0(String coarse_aggregate01_grading_massfrac_0) {
        this.coarse_aggregate01_grading_massfrac_0 = coarse_aggregate01_grading_massfrac_0;
    }
    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_1.
     */
    private String coarse_aggregate01_grading_massfrac_1;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_1.
     * @return Value of property coarse_aggregate01_grading_massfrac_1.
     */
    public String getCoarse_aggregate01_grading_massfrac_1() {
        return this.coarse_aggregate01_grading_massfrac_1;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_1.
     * @param coarse_aggregate01_grading_massfrac_1 New value of property coarse_aggregate01_grading_massfrac_1.
     */
    public void setCoarse_aggregate01_grading_massfrac_1(String coarse_aggregate01_grading_massfrac_1) {
        this.coarse_aggregate01_grading_massfrac_1 = coarse_aggregate01_grading_massfrac_1;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_2.
     */
    private String coarse_aggregate01_grading_massfrac_2;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_2.
     * @return Value of property coarse_aggregate01_grading_massfrac_2.
     */
    public String getCoarse_aggregate01_grading_massfrac_2() {
        return this.coarse_aggregate01_grading_massfrac_2;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_2.
     * @param coarse_aggregate01_grading_massfrac_2 New value of property coarse_aggregate01_grading_massfrac_2.
     */
    public void setCoarse_aggregate01_grading_massfrac_2(String coarse_aggregate01_grading_massfrac_2) {
        this.coarse_aggregate01_grading_massfrac_2 = coarse_aggregate01_grading_massfrac_2;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_3.
     */
    private String coarse_aggregate01_grading_massfrac_3;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_3.
     * @return Value of property coarse_aggregate01_grading_massfrac_3.
     */
    public String getCoarse_aggregate01_grading_massfrac_3() {
        return this.coarse_aggregate01_grading_massfrac_3;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_3.
     * @param coarse_aggregate01_grading_massfrac_3 New value of property coarse_aggregate01_grading_massfrac_3.
     */
    public void setCoarse_aggregate01_grading_massfrac_3(String coarse_aggregate01_grading_massfrac_3) {
        this.coarse_aggregate01_grading_massfrac_3 = coarse_aggregate01_grading_massfrac_3;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_4.
     */
    private String coarse_aggregate01_grading_massfrac_4;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_4.
     * @return Value of property coarse_aggregate01_grading_massfrac_4.
     */
    public String getCoarse_aggregate01_grading_massfrac_4() {
        return this.coarse_aggregate01_grading_massfrac_4;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_4.
     * @param coarse_aggregate01_grading_massfrac_4 New value of property coarse_aggregate01_grading_massfrac_4.
     */
    public void setCoarse_aggregate01_grading_massfrac_4(String coarse_aggregate01_grading_massfrac_4) {
        this.coarse_aggregate01_grading_massfrac_4 = coarse_aggregate01_grading_massfrac_4;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_5.
     */
    private String coarse_aggregate01_grading_massfrac_5;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_5.
     * @return Value of property coarse_aggregate01_grading_massfrac_5.
     */
    public String getCoarse_aggregate01_grading_massfrac_5() {
        return this.coarse_aggregate01_grading_massfrac_5;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_5.
     * @param coarse_aggregate01_grading_massfrac_5 New value of property coarse_aggregate01_grading_massfrac_5.
     */
    public void setCoarse_aggregate01_grading_massfrac_5(String coarse_aggregate01_grading_massfrac_5) {
        this.coarse_aggregate01_grading_massfrac_5 = coarse_aggregate01_grading_massfrac_5;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_6.
     */
    private String coarse_aggregate01_grading_massfrac_6;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_6.
     * @return Value of property coarse_aggregate01_grading_massfrac_6.
     */
    public String getCoarse_aggregate01_grading_massfrac_6() {
        return this.coarse_aggregate01_grading_massfrac_6;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_6.
     * @param coarse_aggregate01_grading_massfrac_6 New value of property coarse_aggregate01_grading_massfrac_6.
     */
    public void setCoarse_aggregate01_grading_massfrac_6(String coarse_aggregate01_grading_massfrac_6) {
        this.coarse_aggregate01_grading_massfrac_6 = coarse_aggregate01_grading_massfrac_6;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_7.
     */
    private String coarse_aggregate01_grading_massfrac_7;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_7.
     * @return Value of property coarse_aggregate01_grading_massfrac_7.
     */
    public String getCoarse_aggregate01_grading_massfrac_7() {
        return this.coarse_aggregate01_grading_massfrac_7;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_7.
     * @param coarse_aggregate01_grading_massfrac_7 New value of property coarse_aggregate01_grading_massfrac_7.
     */
    public void setCoarse_aggregate01_grading_massfrac_7(String coarse_aggregate01_grading_massfrac_7) {
        this.coarse_aggregate01_grading_massfrac_7 = coarse_aggregate01_grading_massfrac_7;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_8.
     */
    private String coarse_aggregate01_grading_massfrac_8;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_8.
     * @return Value of property coarse_aggregate01_grading_massfrac_8.
     */
    public String getCoarse_aggregate01_grading_massfrac_8() {
        return this.coarse_aggregate01_grading_massfrac_8;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_8.
     * @param coarse_aggregate01_grading_massfrac_8 New value of property coarse_aggregate01_grading_massfrac_8.
     */
    public void setCoarse_aggregate01_grading_massfrac_8(String coarse_aggregate01_grading_massfrac_8) {
        this.coarse_aggregate01_grading_massfrac_8 = coarse_aggregate01_grading_massfrac_8;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_9.
     */
    private String coarse_aggregate01_grading_massfrac_9;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_9.
     * @return Value of property coarse_aggregate01_grading_massfrac_9.
     */
    public String getCoarse_aggregate01_grading_massfrac_9() {
        return this.coarse_aggregate01_grading_massfrac_9;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_9.
     * @param coarse_aggregate01_grading_massfrac_9 New value of property coarse_aggregate01_grading_massfrac_9.
     */
    public void setCoarse_aggregate01_grading_massfrac_9(String coarse_aggregate01_grading_massfrac_9) {
        this.coarse_aggregate01_grading_massfrac_9 = coarse_aggregate01_grading_massfrac_9;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_10.
     */
    private String coarse_aggregate01_grading_massfrac_10;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_10.
     * @return Value of property coarse_aggregate01_grading_massfrac_10.
     */
    public String getCoarse_aggregate01_grading_massfrac_10() {
        return this.coarse_aggregate01_grading_massfrac_10;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_10.
     * @param coarse_aggregate01_grading_massfrac_10 New value of property coarse_aggregate01_grading_massfrac_10.
     */
    public void setCoarse_aggregate01_grading_massfrac_10(String coarse_aggregate01_grading_massfrac_10) {
        this.coarse_aggregate01_grading_massfrac_10 = coarse_aggregate01_grading_massfrac_10;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_11.
     */
    private String coarse_aggregate01_grading_massfrac_11;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_11.
     * @return Value of property coarse_aggregate01_grading_massfrac_11.
     */
    public String getCoarse_aggregate01_grading_massfrac_11() {
        return this.coarse_aggregate01_grading_massfrac_11;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_11.
     * @param coarse_aggregate01_grading_massfrac_11 New value of property coarse_aggregate01_grading_massfrac_11.
     */
    public void setCoarse_aggregate01_grading_massfrac_11(String coarse_aggregate01_grading_massfrac_11) {
        this.coarse_aggregate01_grading_massfrac_11 = coarse_aggregate01_grading_massfrac_11;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_12.
     */
    private String coarse_aggregate01_grading_massfrac_12;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_12.
     * @return Value of property coarse_aggregate01_grading_massfrac_12.
     */
    public String getCoarse_aggregate01_grading_massfrac_12() {
        return this.coarse_aggregate01_grading_massfrac_12;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_12.
     * @param coarse_aggregate01_grading_massfrac_12 New value of property coarse_aggregate01_grading_massfrac_12.
     */
    public void setCoarse_aggregate01_grading_massfrac_12(String coarse_aggregate01_grading_massfrac_12) {
        this.coarse_aggregate01_grading_massfrac_12 = coarse_aggregate01_grading_massfrac_12;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_13.
     */
    private String coarse_aggregate01_grading_massfrac_13;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_13.
     * @return Value of property coarse_aggregate01_grading_massfrac_13.
     */
    public String getCoarse_aggregate01_grading_massfrac_13() {
        return this.coarse_aggregate01_grading_massfrac_13;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_13.
     * @param coarse_aggregate01_grading_massfrac_13 New value of property coarse_aggregate01_grading_massfrac_13.
     */
    public void setCoarse_aggregate01_grading_massfrac_13(String coarse_aggregate01_grading_massfrac_13) {
        this.coarse_aggregate01_grading_massfrac_13 = coarse_aggregate01_grading_massfrac_13;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_14.
     */
    private String coarse_aggregate01_grading_massfrac_14;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_4.
     * @return Value of property coarse_aggregate01_grading_massfrac_4.
     */
    public String getCoarse_aggregate01_grading_massfrac_14() {
        return this.coarse_aggregate01_grading_massfrac_14;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_14.
     * @param coarse_aggregate01_grading_massfrac_14 New value of property coarse_aggregate01_grading_massfrac_14.
     */
    public void setCoarse_aggregate01_grading_massfrac_14(String coarse_aggregate01_grading_massfrac_14) {
        this.coarse_aggregate01_grading_massfrac_14 = coarse_aggregate01_grading_massfrac_14;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_15.
     */
    private String coarse_aggregate01_grading_massfrac_15;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_15.
     * @return Value of property coarse_aggregate01_grading_massfrac_15.
     */
    public String getCoarse_aggregate01_grading_massfrac_15() {
        return this.coarse_aggregate01_grading_massfrac_15;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_15.
     * @param coarse_aggregate01_grading_massfrac_15 New value of property coarse_aggregate01_grading_massfrac_15.
     */
    public void setCoarse_aggregate01_grading_massfrac_15(String coarse_aggregate01_grading_massfrac_15) {
        this.coarse_aggregate01_grading_massfrac_15 = coarse_aggregate01_grading_massfrac_15;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_16.
     */
    private String coarse_aggregate01_grading_massfrac_16;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_16.
     * @return Value of property coarse_aggregate01_grading_massfrac_16.
     */
    public String getCoarse_aggregate01_grading_massfrac_16() {
        return this.coarse_aggregate01_grading_massfrac_16;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_16.
     * @param coarse_aggregate01_grading_massfrac_16 New value of property coarse_aggregate01_grading_massfrac_16.
     */
    public void setCoarse_aggregate01_grading_massfrac_16(String coarse_aggregate01_grading_massfrac_16) {
        this.coarse_aggregate01_grading_massfrac_16 = coarse_aggregate01_grading_massfrac_16;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_17.
     */
    private String coarse_aggregate01_grading_massfrac_17;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_17.
     * @return Value of property coarse_aggregate01_grading_massfrac_17.
     */
    public String getCoarse_aggregate01_grading_massfrac_17() {
        return this.coarse_aggregate01_grading_massfrac_17;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_17.
     * @param coarse_aggregate01_grading_massfrac_17 New value of property coarse_aggregate01_grading_massfrac_17.
     */
    public void setCoarse_aggregate01_grading_massfrac_17(String coarse_aggregate01_grading_massfrac_17) {
        this.coarse_aggregate01_grading_massfrac_17 = coarse_aggregate01_grading_massfrac_17;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_18.
     */
    private String coarse_aggregate01_grading_massfrac_18;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_18.
     * @return Value of property coarse_aggregate01_grading_massfrac_18.
     */
    public String getCoarse_aggregate01_grading_massfrac_18() {
        return this.coarse_aggregate01_grading_massfrac_18;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_18.
     * @param coarse_aggregate01_grading_massfrac_18 New value of property coarse_aggregate01_grading_massfrac_18.
     */
    public void setCoarse_aggregate01_grading_massfrac_18(String coarse_aggregate01_grading_massfrac_18) {
        this.coarse_aggregate01_grading_massfrac_18 = coarse_aggregate01_grading_massfrac_18;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_19.
     */
    private String coarse_aggregate01_grading_massfrac_19;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_19.
     * @return Value of property coarse_aggregate01_grading_massfrac_19.
     */
    public String getCoarse_aggregate01_grading_massfrac_19() {
        return this.coarse_aggregate01_grading_massfrac_19;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_19.
     * @param coarse_aggregate01_grading_massfrac_19 New value of property coarse_aggregate01_grading_massfrac_19.
     */
    public void setCoarse_aggregate01_grading_massfrac_19(String coarse_aggregate01_grading_massfrac_19) {
        this.coarse_aggregate01_grading_massfrac_19 = coarse_aggregate01_grading_massfrac_19;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_20.
     */
    private String coarse_aggregate01_grading_massfrac_20;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_20.
     * @return Value of property coarse_aggregate01_grading_massfrac_20.
     */
    public String getCoarse_aggregate01_grading_massfrac_20() {
        return this.coarse_aggregate01_grading_massfrac_20;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_20.
     * @param coarse_aggregate01_grading_massfrac_20 New value of property coarse_aggregate01_grading_massfrac_20.
     */
    public void setCoarse_aggregate01_grading_massfrac_20(String coarse_aggregate01_grading_massfrac_20) {
        this.coarse_aggregate01_grading_massfrac_20 = coarse_aggregate01_grading_massfrac_20;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_21.
     */
    private String coarse_aggregate01_grading_massfrac_21;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_21.
     * @return Value of property coarse_aggregate01_grading_massfrac_21.
     */
    public String getCoarse_aggregate01_grading_massfrac_21() {
        return this.coarse_aggregate01_grading_massfrac_21;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_21.
     * @param coarse_aggregate01_grading_massfrac_21 New value of property coarse_aggregate01_grading_massfrac_21.
     */
    public void setCoarse_aggregate01_grading_massfrac_21(String coarse_aggregate01_grading_massfrac_21) {
        this.coarse_aggregate01_grading_massfrac_21 = coarse_aggregate01_grading_massfrac_21;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_massfrac_22.
     */
    private String coarse_aggregate01_grading_massfrac_22;

    /**
     * Getter for property coarse_aggregate01_grading_massfrac_22.
     * @return Value of property coarse_aggregate01_grading_massfrac_22.
     */
    public String getCoarse_aggregate01_grading_massfrac_22() {
        return this.coarse_aggregate01_grading_massfrac_22;
    }

    /**
     * Setter for property coarse_aggregate01_grading_massfrac_22.
     * @param coarse_aggregate01_grading_massfrac_22 New value of property coarse_aggregate01_grading_massfrac_22.
     */
    public void setCoarse_aggregate01_grading_massfrac_22(String coarse_aggregate01_grading_massfrac_22) {
        this.coarse_aggregate01_grading_massfrac_22 = coarse_aggregate01_grading_massfrac_22;
    }

    /**
     * Holds value of property coarse_aggregate01_grading_total_massfrac.
     */
    private String coarse_aggregate01_grading_total_massfrac;

    /**
     * Getter for property coarse_aggregate01_grading_total_massfrac.
     * @return Value of property coarse_aggregate01_grading_total_massfrac.
     */
    public String getCoarse_aggregate01_grading_total_massfrac() {
        return this.coarse_aggregate01_grading_total_massfrac;
    }

    /**
     * Setter for property coarse_aggregate01_grading_total_massfrac.
     * @param coarse_aggregate01_grading_total_massfrac New value of property coarse_aggregate01_grading_total_massfrac.
     */
    public void setCoarse_aggregate01_grading_total_massfrac(String coarse_aggregate01_grading_total_massfrac) {
        this.coarse_aggregate01_grading_total_massfrac = coarse_aggregate01_grading_total_massfrac;
    }

     /**
     * Holds value of property fine_aggregate01_grading_massfrac_0.
     */
    private String fine_aggregate01_grading_massfrac_0;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_0.
     * @return Value of property fine_aggregate01_grading_massfrac_0.
     */
    public String getFine_aggregate01_grading_massfrac_0() {
        return this.fine_aggregate01_grading_massfrac_0;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_0.
     * @param fine_aggregate01_grading_massfrac_0 New value of property fine_aggregate01_grading_massfrac_0.
     */
    public void setFine_aggregate01_grading_massfrac_0(String fine_aggregate01_grading_massfrac_0) {
        this.fine_aggregate01_grading_massfrac_0 = fine_aggregate01_grading_massfrac_0;
    }
    /**
     * Holds value of property fine_aggregate01_grading_massfrac_1.
     */
    private String fine_aggregate01_grading_massfrac_1;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_1.
     * @return Value of property fine_aggregate01_grading_massfrac_1.
     */
    public String getFine_aggregate01_grading_massfrac_1() {
        return this.fine_aggregate01_grading_massfrac_1;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_1.
     * @param fine_aggregate01_grading_massfrac_1 New value of property fine_aggregate01_grading_massfrac_1.
     */
    public void setFine_aggregate01_grading_massfrac_1(String fine_aggregate01_grading_massfrac_1) {
        this.fine_aggregate01_grading_massfrac_1 = fine_aggregate01_grading_massfrac_1;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_2.
     */
    private String fine_aggregate01_grading_massfrac_2;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_2.
     * @return Value of property fine_aggregate01_grading_massfrac_2.
     */
    public String getFine_aggregate01_grading_massfrac_2() {
        return this.fine_aggregate01_grading_massfrac_2;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_2.
     * @param fine_aggregate01_grading_massfrac_2 New value of property fine_aggregate01_grading_massfrac_2.
     */
    public void setFine_aggregate01_grading_massfrac_2(String fine_aggregate01_grading_massfrac_2) {
        this.fine_aggregate01_grading_massfrac_2 = fine_aggregate01_grading_massfrac_2;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_3.
     */
    private String fine_aggregate01_grading_massfrac_3;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_3.
     * @return Value of property fine_aggregate01_grading_massfrac_3.
     */
    public String getFine_aggregate01_grading_massfrac_3() {
        return this.fine_aggregate01_grading_massfrac_3;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_3.
     * @param fine_aggregate01_grading_massfrac_3 New value of property fine_aggregate01_grading_massfrac_3.
     */
    public void setFine_aggregate01_grading_massfrac_3(String fine_aggregate01_grading_massfrac_3) {
        this.fine_aggregate01_grading_massfrac_3 = fine_aggregate01_grading_massfrac_3;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_4.
     */
    private String fine_aggregate01_grading_massfrac_4;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_4.
     * @return Value of property fine_aggregate01_grading_massfrac_4.
     */
    public String getFine_aggregate01_grading_massfrac_4() {
        return this.fine_aggregate01_grading_massfrac_4;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_4.
     * @param fine_aggregate01_grading_massfrac_4 New value of property fine_aggregate01_grading_massfrac_4.
     */
    public void setFine_aggregate01_grading_massfrac_4(String fine_aggregate01_grading_massfrac_4) {
        this.fine_aggregate01_grading_massfrac_4 = fine_aggregate01_grading_massfrac_4;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_5.
     */
    private String fine_aggregate01_grading_massfrac_5;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_5.
     * @return Value of property fine_aggregate01_grading_massfrac_5.
     */
    public String getFine_aggregate01_grading_massfrac_5() {
        return this.fine_aggregate01_grading_massfrac_5;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_5.
     * @param fine_aggregate01_grading_massfrac_5 New value of property fine_aggregate01_grading_massfrac_5.
     */
    public void setFine_aggregate01_grading_massfrac_5(String fine_aggregate01_grading_massfrac_5) {
        this.fine_aggregate01_grading_massfrac_5 = fine_aggregate01_grading_massfrac_5;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_6.
     */
    private String fine_aggregate01_grading_massfrac_6;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_6.
     * @return Value of property fine_aggregate01_grading_massfrac_6.
     */
    public String getFine_aggregate01_grading_massfrac_6() {
        return this.fine_aggregate01_grading_massfrac_6;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_6.
     * @param fine_aggregate01_grading_massfrac_6 New value of property fine_aggregate01_grading_massfrac_6.
     */
    public void setFine_aggregate01_grading_massfrac_6(String fine_aggregate01_grading_massfrac_6) {
        this.fine_aggregate01_grading_massfrac_6 = fine_aggregate01_grading_massfrac_6;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_7.
     */
    private String fine_aggregate01_grading_massfrac_7;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_7.
     * @return Value of property fine_aggregate01_grading_massfrac_7.
     */
    public String getFine_aggregate01_grading_massfrac_7() {
        return this.fine_aggregate01_grading_massfrac_7;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_7.
     * @param fine_aggregate01_grading_massfrac_7 New value of property fine_aggregate01_grading_massfrac_7.
     */
    public void setFine_aggregate01_grading_massfrac_7(String fine_aggregate01_grading_massfrac_7) {
        this.fine_aggregate01_grading_massfrac_7 = fine_aggregate01_grading_massfrac_7;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_8.
     */
    private String fine_aggregate01_grading_massfrac_8;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_8.
     * @return Value of property fine_aggregate01_grading_massfrac_8.
     */
    public String getFine_aggregate01_grading_massfrac_8() {
        return this.fine_aggregate01_grading_massfrac_8;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_8.
     * @param fine_aggregate01_grading_massfrac_8 New value of property fine_aggregate01_grading_massfrac_8.
     */
    public void setFine_aggregate01_grading_massfrac_8(String fine_aggregate01_grading_massfrac_8) {
        this.fine_aggregate01_grading_massfrac_8 = fine_aggregate01_grading_massfrac_8;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_9.
     */
    private String fine_aggregate01_grading_massfrac_9;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_9.
     * @return Value of property fine_aggregate01_grading_massfrac_9.
     */
    public String getFine_aggregate01_grading_massfrac_9() {
        return this.fine_aggregate01_grading_massfrac_9;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_9.
     * @param fine_aggregate01_grading_massfrac_9 New value of property fine_aggregate01_grading_massfrac_9.
     */
    public void setFine_aggregate01_grading_massfrac_9(String fine_aggregate01_grading_massfrac_9) {
        this.fine_aggregate01_grading_massfrac_9 = fine_aggregate01_grading_massfrac_9;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_10.
     */
    private String fine_aggregate01_grading_massfrac_10;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_10.
     * @return Value of property fine_aggregate01_grading_massfrac_10.
     */
    public String getFine_aggregate01_grading_massfrac_10() {
        return this.fine_aggregate01_grading_massfrac_10;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_10.
     * @param fine_aggregate01_grading_massfrac_10 New value of property fine_aggregate01_grading_massfrac_10.
     */
    public void setFine_aggregate01_grading_massfrac_10(String fine_aggregate01_grading_massfrac_10) {
        this.fine_aggregate01_grading_massfrac_10 = fine_aggregate01_grading_massfrac_10;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_11.
     */
    private String fine_aggregate01_grading_massfrac_11;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_11.
     * @return Value of property fine_aggregate01_grading_massfrac_11.
     */
    public String getFine_aggregate01_grading_massfrac_11() {
        return this.fine_aggregate01_grading_massfrac_11;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_11.
     * @param fine_aggregate01_grading_massfrac_11 New value of property fine_aggregate01_grading_massfrac_11.
     */
    public void setFine_aggregate01_grading_massfrac_11(String fine_aggregate01_grading_massfrac_11) {
        this.fine_aggregate01_grading_massfrac_11 = fine_aggregate01_grading_massfrac_11;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_12.
     */
    private String fine_aggregate01_grading_massfrac_12;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_12.
     * @return Value of property fine_aggregate01_grading_massfrac_12.
     */
    public String getFine_aggregate01_grading_massfrac_12() {
        return this.fine_aggregate01_grading_massfrac_12;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_12.
     * @param fine_aggregate01_grading_massfrac_12 New value of property fine_aggregate01_grading_massfrac_12.
     */
    public void setFine_aggregate01_grading_massfrac_12(String fine_aggregate01_grading_massfrac_12) {
        this.fine_aggregate01_grading_massfrac_12 = fine_aggregate01_grading_massfrac_12;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_13.
     */
    private String fine_aggregate01_grading_massfrac_13;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_13.
     * @return Value of property fine_aggregate01_grading_massfrac_13.
     */
    public String getFine_aggregate01_grading_massfrac_13() {
        return this.fine_aggregate01_grading_massfrac_13;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_13.
     * @param fine_aggregate01_grading_massfrac_13 New value of property fine_aggregate01_grading_massfrac_13.
     */
    public void setFine_aggregate01_grading_massfrac_13(String fine_aggregate01_grading_massfrac_13) {
        this.fine_aggregate01_grading_massfrac_13 = fine_aggregate01_grading_massfrac_13;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_14.
     */
    private String fine_aggregate01_grading_massfrac_14;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_4.
     * @return Value of property fine_aggregate01_grading_massfrac_4.
     */
    public String getFine_aggregate01_grading_massfrac_14() {
        return this.fine_aggregate01_grading_massfrac_14;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_14.
     * @param fine_aggregate01_grading_massfrac_14 New value of property fine_aggregate01_grading_massfrac_14.
     */
    public void setFine_aggregate01_grading_massfrac_14(String fine_aggregate01_grading_massfrac_14) {
        this.fine_aggregate01_grading_massfrac_14 = fine_aggregate01_grading_massfrac_14;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_15.
     */
    private String fine_aggregate01_grading_massfrac_15;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_15.
     * @return Value of property fine_aggregate01_grading_massfrac_15.
     */
    public String getFine_aggregate01_grading_massfrac_15() {
        return this.fine_aggregate01_grading_massfrac_15;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_15.
     * @param fine_aggregate01_grading_massfrac_15 New value of property fine_aggregate01_grading_massfrac_15.
     */
    public void setFine_aggregate01_grading_massfrac_15(String fine_aggregate01_grading_massfrac_15) {
        this.fine_aggregate01_grading_massfrac_15 = fine_aggregate01_grading_massfrac_15;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_16.
     */
    private String fine_aggregate01_grading_massfrac_16;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_16.
     * @return Value of property fine_aggregate01_grading_massfrac_16.
     */
    public String getFine_aggregate01_grading_massfrac_16() {
        return this.fine_aggregate01_grading_massfrac_16;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_16.
     * @param fine_aggregate01_grading_massfrac_16 New value of property fine_aggregate01_grading_massfrac_16.
     */
    public void setFine_aggregate01_grading_massfrac_16(String fine_aggregate01_grading_massfrac_16) {
        this.fine_aggregate01_grading_massfrac_16 = fine_aggregate01_grading_massfrac_16;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_17.
     */
    private String fine_aggregate01_grading_massfrac_17;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_17.
     * @return Value of property fine_aggregate01_grading_massfrac_17.
     */
    public String getFine_aggregate01_grading_massfrac_17() {
        return this.fine_aggregate01_grading_massfrac_17;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_17.
     * @param fine_aggregate01_grading_massfrac_17 New value of property fine_aggregate01_grading_massfrac_17.
     */
    public void setFine_aggregate01_grading_massfrac_17(String fine_aggregate01_grading_massfrac_17) {
        this.fine_aggregate01_grading_massfrac_17 = fine_aggregate01_grading_massfrac_17;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_18.
     */
    private String fine_aggregate01_grading_massfrac_18;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_18.
     * @return Value of property fine_aggregate01_grading_massfrac_18.
     */
    public String getFine_aggregate01_grading_massfrac_18() {
        return this.fine_aggregate01_grading_massfrac_18;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_18.
     * @param fine_aggregate01_grading_massfrac_18 New value of property fine_aggregate01_grading_massfrac_18.
     */
    public void setFine_aggregate01_grading_massfrac_18(String fine_aggregate01_grading_massfrac_18) {
        this.fine_aggregate01_grading_massfrac_18 = fine_aggregate01_grading_massfrac_18;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_19.
     */
    private String fine_aggregate01_grading_massfrac_19;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_19.
     * @return Value of property fine_aggregate01_grading_massfrac_19.
     */
    public String getFine_aggregate01_grading_massfrac_19() {
        return this.fine_aggregate01_grading_massfrac_19;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_19.
     * @param fine_aggregate01_grading_massfrac_19 New value of property fine_aggregate01_grading_massfrac_19.
     */
    public void setFine_aggregate01_grading_massfrac_19(String fine_aggregate01_grading_massfrac_19) {
        this.fine_aggregate01_grading_massfrac_19 = fine_aggregate01_grading_massfrac_19;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_20.
     */
    private String fine_aggregate01_grading_massfrac_20;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_20.
     * @return Value of property fine_aggregate01_grading_massfrac_20.
     */
    public String getFine_aggregate01_grading_massfrac_20() {
        return this.fine_aggregate01_grading_massfrac_20;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_20.
     * @param fine_aggregate01_grading_massfrac_20 New value of property fine_aggregate01_grading_massfrac_20.
     */
    public void setFine_aggregate01_grading_massfrac_20(String fine_aggregate01_grading_massfrac_20) {
        this.fine_aggregate01_grading_massfrac_20 = fine_aggregate01_grading_massfrac_20;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_21.
     */
    private String fine_aggregate01_grading_massfrac_21;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_21.
     * @return Value of property fine_aggregate01_grading_massfrac_21.
     */
    public String getFine_aggregate01_grading_massfrac_21() {
        return this.fine_aggregate01_grading_massfrac_21;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_21.
     * @param fine_aggregate01_grading_massfrac_21 New value of property fine_aggregate01_grading_massfrac_21.
     */
    public void setFine_aggregate01_grading_massfrac_21(String fine_aggregate01_grading_massfrac_21) {
        this.fine_aggregate01_grading_massfrac_21 = fine_aggregate01_grading_massfrac_21;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_22.
     */
    private String fine_aggregate01_grading_massfrac_22;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_22.
     * @return Value of property fine_aggregate01_grading_massfrac_22.
     */
    public String getFine_aggregate01_grading_massfrac_22() {
        return this.fine_aggregate01_grading_massfrac_22;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_22.
     * @param fine_aggregate01_grading_massfrac_22 New value of property fine_aggregate01_grading_massfrac_22.
     */
    public void setFine_aggregate01_grading_massfrac_22(String fine_aggregate01_grading_massfrac_22) {
        this.fine_aggregate01_grading_massfrac_22 = fine_aggregate01_grading_massfrac_22;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_23.
     */
    private String fine_aggregate01_grading_massfrac_23;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_23.
     * @return Value of property fine_aggregate01_grading_massfrac_23.
     */
    public String getFine_aggregate01_grading_massfrac_23() {
        return this.fine_aggregate01_grading_massfrac_23;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_23.
     * @param fine_aggregate01_grading_massfrac_23 New value of property fine_aggregate01_grading_massfrac_23.
     */
    public void setFine_aggregate01_grading_massfrac_23(String fine_aggregate01_grading_massfrac_23) {
        this.fine_aggregate01_grading_massfrac_23 = fine_aggregate01_grading_massfrac_23;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_24.
     */
    private String fine_aggregate01_grading_massfrac_24;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_24.
     * @return Value of property fine_aggregate01_grading_massfrac_24.
     */
    public String getFine_aggregate01_grading_massfrac_24() {
        return this.fine_aggregate01_grading_massfrac_24;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_24.
     * @param fine_aggregate01_grading_massfrac_24 New value of property fine_aggregate01_grading_massfrac_24.
     */
    public void setFine_aggregate01_grading_massfrac_24(String fine_aggregate01_grading_massfrac_24) {
        this.fine_aggregate01_grading_massfrac_24 = fine_aggregate01_grading_massfrac_24;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_25.
     */
    private String fine_aggregate01_grading_massfrac_25;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_25.
     * @return Value of property fine_aggregate01_grading_massfrac_25.
     */
    public String getFine_aggregate01_grading_massfrac_25() {
        return this.fine_aggregate01_grading_massfrac_25;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_25.
     * @param fine_aggregate01_grading_massfrac_25 New value of property fine_aggregate01_grading_massfrac_25.
     */
    public void setFine_aggregate01_grading_massfrac_25(String fine_aggregate01_grading_massfrac_25) {
        this.fine_aggregate01_grading_massfrac_25 = fine_aggregate01_grading_massfrac_25;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_26.
     */
    private String fine_aggregate01_grading_massfrac_26;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_26.
     * @return Value of property fine_aggregate01_grading_massfrac_26.
     */
    public String getFine_aggregate01_grading_massfrac_26() {
        return this.fine_aggregate01_grading_massfrac_26;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_26.
     * @param fine_aggregate01_grading_massfrac_26 New value of property fine_aggregate01_grading_massfrac_26.
     */
    public void setFine_aggregate01_grading_massfrac_26(String fine_aggregate01_grading_massfrac_26) {
        this.fine_aggregate01_grading_massfrac_26 = fine_aggregate01_grading_massfrac_26;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_27.
     */
    private String fine_aggregate01_grading_massfrac_27;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_27.
     * @return Value of property fine_aggregate01_grading_massfrac_27.
     */
    public String getFine_aggregate01_grading_massfrac_27() {
        return this.fine_aggregate01_grading_massfrac_27;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_27.
     * @param fine_aggregate01_grading_massfrac_27 New value of property fine_aggregate01_grading_massfrac_27.
     */
    public void setFine_aggregate01_grading_massfrac_27(String fine_aggregate01_grading_massfrac_27) {
        this.fine_aggregate01_grading_massfrac_27 = fine_aggregate01_grading_massfrac_27;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_28.
     */
    private String fine_aggregate01_grading_massfrac_28;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_28.
     * @return Value of property fine_aggregate01_grading_massfrac_28.
     */
    public String getFine_aggregate01_grading_massfrac_28() {
        return this.fine_aggregate01_grading_massfrac_28;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_28.
     * @param fine_aggregate01_grading_massfrac_28 New value of property fine_aggregate01_grading_massfrac_28.
     */
    public void setFine_aggregate01_grading_massfrac_28(String fine_aggregate01_grading_massfrac_28) {
        this.fine_aggregate01_grading_massfrac_28 = fine_aggregate01_grading_massfrac_28;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_29.
     */
    private String fine_aggregate01_grading_massfrac_29;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_29.
     * @return Value of property fine_aggregate01_grading_massfrac_29.
     */
    public String getFine_aggregate01_grading_massfrac_29() {
        return this.fine_aggregate01_grading_massfrac_29;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_29.
     * @param fine_aggregate01_grading_massfrac_29 New value of property fine_aggregate01_grading_massfrac_29.
     */
    public void setFine_aggregate01_grading_massfrac_29(String fine_aggregate01_grading_massfrac_29) {
        this.fine_aggregate01_grading_massfrac_29 = fine_aggregate01_grading_massfrac_29;
    }

    /**
     * Holds value of property fine_aggregate01_grading_massfrac_30.
     */
    private String fine_aggregate01_grading_massfrac_30;

    /**
     * Getter for property fine_aggregate01_grading_massfrac_30.
     * @return Value of property fine_aggregate01_grading_massfrac_30.
     */
    public String getFine_aggregate01_grading_massfrac_30() {
        return this.fine_aggregate01_grading_massfrac_30;
    }

    /**
     * Setter for property fine_aggregate01_grading_massfrac_30.
     * @param fine_aggregate01_grading_massfrac_30 New value of property fine_aggregate01_grading_massfrac_30.
     */
    public void setFine_aggregate01_grading_massfrac_30(String fine_aggregate01_grading_massfrac_30) {
        this.fine_aggregate01_grading_massfrac_30 = fine_aggregate01_grading_massfrac_30;
    }

     /**
     * Get the data grading of the fine aggregate 02
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getFine02GradingFromDatabase() throws SQLArgumentException, SQLException {
        return getGradingFromDatabase(fine_aggregate02_grading_name);
    }

    /**
     * Get the data grading of the coarse aggregate 02
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getCoarse02GradingFromDatabase() throws SQLArgumentException, SQLException {
        return getGradingFromDatabase(coarse_aggregate02_grading_name);
    }

    /**
     * Get the data grading of the fine aggregate 02
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getFine02Grading() {
        return getGradingFromString(fine_aggregate02_grading);
    }

    /**
     * Get the data grading of the coarse aggregate 02
     * The first row of the result contains the sieve names
     * The second row of the result contains the diameters corresponding to the sieve names
     * The third row contains the mass fractions corresponding to the sieves
     * @return Data grading
     **/
    public String[][] getCoarse02Grading() {
        return getGradingFromString(coarse_aggregate02_grading);
    }

    /**
     * Holds value of property fine_aggregate02_grading_max_diam.
     */
    private String fine_aggregate02_grading_max_diam;

    /**
     * Getter for property fine_aggregate02_grading_max_diam.
     * @return Value of property fine_aggregate02_grading_max_diam.
     */
    public String getFine_aggregate02_grading_max_diam() {
        return this.fine_aggregate02_grading_max_diam;
    }

    /**
     * Setter for property fine_aggregate02_grading_max_diam.
     * @param fine_aggregate_grading01_max_diam New value of property fine_aggregate02_grading_max_diam.
     */
    public void setFine_aggregate02_grading_max_diam(String fine_aggregate02_grading_max_diam) {
        this.fine_aggregate02_grading_max_diam = fine_aggregate02_grading_max_diam;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_max_diam.
     */
    private String coarse_aggregate02_grading_max_diam;

    /**
     * Getter for property coarse_aggregate02_grading_max_diam.
     * @return Value of property coarse_aggregate02_grading_max_diam.
     */
    public String getCoarse_aggregate02_grading_max_diam() {
        return this.coarse_aggregate02_grading_max_diam;
    }

    /**
     * Setter for property coarse_aggregate02_grading_max_diam.
     * @param coarse_aggregate02_grading_max_diam New value of property coarse_aggregate02_grading_max_diam.
     */
    public void setCoarse_aggregate02_grading_max_diam(String coarse_aggregate02_grading_max_diam) {
        this.coarse_aggregate02_grading_max_diam = coarse_aggregate02_grading_max_diam;
    }

     /**
     * Holds value of property coarse_aggregate02_grading_massfrac_0.
     */
    private String coarse_aggregate02_grading_massfrac_0;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_0.
     * @return Value of property coarse_aggregate02_grading_massfrac_0.
     */
    public String getCoarse_aggregate02_grading_massfrac_0() {
        return this.coarse_aggregate02_grading_massfrac_0;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_0.
     * @param coarse_aggregate02_grading_massfrac_0 New value of property coarse_aggregate02_grading_massfrac_0.
     */
    public void setCoarse_aggregate02_grading_massfrac_0(String coarse_aggregate02_grading_massfrac_0) {
        this.coarse_aggregate02_grading_massfrac_0 = coarse_aggregate02_grading_massfrac_0;
    }
    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_1.
     */
    private String coarse_aggregate02_grading_massfrac_1;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_1.
     * @return Value of property coarse_aggregate02_grading_massfrac_1.
     */
    public String getCoarse_aggregate02_grading_massfrac_1() {
        return this.coarse_aggregate02_grading_massfrac_1;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_1.
     * @param coarse_aggregate02_grading_massfrac_1 New value of property coarse_aggregate02_grading_massfrac_1.
     */
    public void setCoarse_aggregate02_grading_massfrac_1(String coarse_aggregate02_grading_massfrac_1) {
        this.coarse_aggregate02_grading_massfrac_1 = coarse_aggregate02_grading_massfrac_1;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_2.
     */
    private String coarse_aggregate02_grading_massfrac_2;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_2.
     * @return Value of property coarse_aggregate02_grading_massfrac_2.
     */
    public String getCoarse_aggregate02_grading_massfrac_2() {
        return this.coarse_aggregate02_grading_massfrac_2;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_2.
     * @param coarse_aggregate02_grading_massfrac_2 New value of property coarse_aggregate02_grading_massfrac_2.
     */
    public void setCoarse_aggregate02_grading_massfrac_2(String coarse_aggregate02_grading_massfrac_2) {
        this.coarse_aggregate02_grading_massfrac_2 = coarse_aggregate02_grading_massfrac_2;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_3.
     */
    private String coarse_aggregate02_grading_massfrac_3;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_3.
     * @return Value of property coarse_aggregate02_grading_massfrac_3.
     */
    public String getCoarse_aggregate02_grading_massfrac_3() {
        return this.coarse_aggregate02_grading_massfrac_3;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_3.
     * @param coarse_aggregate02_grading_massfrac_3 New value of property coarse_aggregate02_grading_massfrac_3.
     */
    public void setCoarse_aggregate02_grading_massfrac_3(String coarse_aggregate02_grading_massfrac_3) {
        this.coarse_aggregate02_grading_massfrac_3 = coarse_aggregate02_grading_massfrac_3;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_4.
     */
    private String coarse_aggregate02_grading_massfrac_4;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_4.
     * @return Value of property coarse_aggregate02_grading_massfrac_4.
     */
    public String getCoarse_aggregate02_grading_massfrac_4() {
        return this.coarse_aggregate02_grading_massfrac_4;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_4.
     * @param coarse_aggregate02_grading_massfrac_4 New value of property coarse_aggregate02_grading_massfrac_4.
     */
    public void setCoarse_aggregate02_grading_massfrac_4(String coarse_aggregate02_grading_massfrac_4) {
        this.coarse_aggregate02_grading_massfrac_4 = coarse_aggregate02_grading_massfrac_4;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_5.
     */
    private String coarse_aggregate02_grading_massfrac_5;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_5.
     * @return Value of property coarse_aggregate02_grading_massfrac_5.
     */
    public String getCoarse_aggregate02_grading_massfrac_5() {
        return this.coarse_aggregate02_grading_massfrac_5;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_5.
     * @param coarse_aggregate02_grading_massfrac_5 New value of property coarse_aggregate02_grading_massfrac_5.
     */
    public void setCoarse_aggregate02_grading_massfrac_5(String coarse_aggregate02_grading_massfrac_5) {
        this.coarse_aggregate02_grading_massfrac_5 = coarse_aggregate02_grading_massfrac_5;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_6.
     */
    private String coarse_aggregate02_grading_massfrac_6;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_6.
     * @return Value of property coarse_aggregate02_grading_massfrac_6.
     */
    public String getCoarse_aggregate02_grading_massfrac_6() {
        return this.coarse_aggregate02_grading_massfrac_6;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_6.
     * @param coarse_aggregate02_grading_massfrac_6 New value of property coarse_aggregate02_grading_massfrac_6.
     */
    public void setCoarse_aggregate02_grading_massfrac_6(String coarse_aggregate02_grading_massfrac_6) {
        this.coarse_aggregate02_grading_massfrac_6 = coarse_aggregate02_grading_massfrac_6;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_7.
     */
    private String coarse_aggregate02_grading_massfrac_7;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_7.
     * @return Value of property coarse_aggregate02_grading_massfrac_7.
     */
    public String getCoarse_aggregate02_grading_massfrac_7() {
        return this.coarse_aggregate02_grading_massfrac_7;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_7.
     * @param coarse_aggregate02_grading_massfrac_7 New value of property coarse_aggregate02_grading_massfrac_7.
     */
    public void setCoarse_aggregate02_grading_massfrac_7(String coarse_aggregate02_grading_massfrac_7) {
        this.coarse_aggregate02_grading_massfrac_7 = coarse_aggregate02_grading_massfrac_7;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_8.
     */
    private String coarse_aggregate02_grading_massfrac_8;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_8.
     * @return Value of property coarse_aggregate02_grading_massfrac_8.
     */
    public String getCoarse_aggregate02_grading_massfrac_8() {
        return this.coarse_aggregate02_grading_massfrac_8;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_8.
     * @param coarse_aggregate02_grading_massfrac_8 New value of property coarse_aggregate02_grading_massfrac_8.
     */
    public void setCoarse_aggregate02_grading_massfrac_8(String coarse_aggregate02_grading_massfrac_8) {
        this.coarse_aggregate02_grading_massfrac_8 = coarse_aggregate02_grading_massfrac_8;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_9.
     */
    private String coarse_aggregate02_grading_massfrac_9;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_9.
     * @return Value of property coarse_aggregate02_grading_massfrac_9.
     */
    public String getCoarse_aggregate02_grading_massfrac_9() {
        return this.coarse_aggregate02_grading_massfrac_9;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_9.
     * @param coarse_aggregate02_grading_massfrac_9 New value of property coarse_aggregate02_grading_massfrac_9.
     */
    public void setCoarse_aggregate02_grading_massfrac_9(String coarse_aggregate02_grading_massfrac_9) {
        this.coarse_aggregate02_grading_massfrac_9 = coarse_aggregate02_grading_massfrac_9;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_10.
     */
    private String coarse_aggregate02_grading_massfrac_10;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_10.
     * @return Value of property coarse_aggregate02_grading_massfrac_10.
     */
    public String getCoarse_aggregate02_grading_massfrac_10() {
        return this.coarse_aggregate02_grading_massfrac_10;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_10.
     * @param coarse_aggregate02_grading_massfrac_10 New value of property coarse_aggregate02_grading_massfrac_10.
     */
    public void setCoarse_aggregate02_grading_massfrac_10(String coarse_aggregate02_grading_massfrac_10) {
        this.coarse_aggregate02_grading_massfrac_10 = coarse_aggregate02_grading_massfrac_10;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_11.
     */
    private String coarse_aggregate02_grading_massfrac_11;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_11.
     * @return Value of property coarse_aggregate02_grading_massfrac_11.
     */
    public String getCoarse_aggregate02_grading_massfrac_11() {
        return this.coarse_aggregate02_grading_massfrac_11;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_11.
     * @param coarse_aggregate02_grading_massfrac_11 New value of property coarse_aggregate02_grading_massfrac_11.
     */
    public void setCoarse_aggregate02_grading_massfrac_11(String coarse_aggregate02_grading_massfrac_11) {
        this.coarse_aggregate02_grading_massfrac_11 = coarse_aggregate02_grading_massfrac_11;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_12.
     */
    private String coarse_aggregate02_grading_massfrac_12;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_12.
     * @return Value of property coarse_aggregate02_grading_massfrac_12.
     */
    public String getCoarse_aggregate02_grading_massfrac_12() {
        return this.coarse_aggregate02_grading_massfrac_12;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_12.
     * @param coarse_aggregate02_grading_massfrac_12 New value of property coarse_aggregate02_grading_massfrac_12.
     */
    public void setCoarse_aggregate02_grading_massfrac_12(String coarse_aggregate02_grading_massfrac_12) {
        this.coarse_aggregate02_grading_massfrac_12 = coarse_aggregate02_grading_massfrac_12;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_13.
     */
    private String coarse_aggregate02_grading_massfrac_13;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_13.
     * @return Value of property coarse_aggregate02_grading_massfrac_13.
     */
    public String getCoarse_aggregate02_grading_massfrac_13() {
        return this.coarse_aggregate02_grading_massfrac_13;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_13.
     * @param coarse_aggregate02_grading_massfrac_13 New value of property coarse_aggregate02_grading_massfrac_13.
     */
    public void setCoarse_aggregate02_grading_massfrac_13(String coarse_aggregate02_grading_massfrac_13) {
        this.coarse_aggregate02_grading_massfrac_13 = coarse_aggregate02_grading_massfrac_13;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_14.
     */
    private String coarse_aggregate02_grading_massfrac_14;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_4.
     * @return Value of property coarse_aggregate02_grading_massfrac_4.
     */
    public String getCoarse_aggregate02_grading_massfrac_14() {
        return this.coarse_aggregate02_grading_massfrac_14;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_14.
     * @param coarse_aggregate02_grading_massfrac_14 New value of property coarse_aggregate02_grading_massfrac_14.
     */
    public void setCoarse_aggregate02_grading_massfrac_14(String coarse_aggregate02_grading_massfrac_14) {
        this.coarse_aggregate02_grading_massfrac_14 = coarse_aggregate02_grading_massfrac_14;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_15.
     */
    private String coarse_aggregate02_grading_massfrac_15;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_15.
     * @return Value of property coarse_aggregate02_grading_massfrac_15.
     */
    public String getCoarse_aggregate02_grading_massfrac_15() {
        return this.coarse_aggregate02_grading_massfrac_15;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_15.
     * @param coarse_aggregate02_grading_massfrac_15 New value of property coarse_aggregate02_grading_massfrac_15.
     */
    public void setCoarse_aggregate02_grading_massfrac_15(String coarse_aggregate02_grading_massfrac_15) {
        this.coarse_aggregate02_grading_massfrac_15 = coarse_aggregate02_grading_massfrac_15;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_16.
     */
    private String coarse_aggregate02_grading_massfrac_16;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_16.
     * @return Value of property coarse_aggregate02_grading_massfrac_16.
     */
    public String getCoarse_aggregate02_grading_massfrac_16() {
        return this.coarse_aggregate02_grading_massfrac_16;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_16.
     * @param coarse_aggregate02_grading_massfrac_16 New value of property coarse_aggregate02_grading_massfrac_16.
     */
    public void setCoarse_aggregate02_grading_massfrac_16(String coarse_aggregate02_grading_massfrac_16) {
        this.coarse_aggregate02_grading_massfrac_16 = coarse_aggregate02_grading_massfrac_16;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_17.
     */
    private String coarse_aggregate02_grading_massfrac_17;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_17.
     * @return Value of property coarse_aggregate02_grading_massfrac_17.
     */
    public String getCoarse_aggregate02_grading_massfrac_17() {
        return this.coarse_aggregate02_grading_massfrac_17;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_17.
     * @param coarse_aggregate02_grading_massfrac_17 New value of property coarse_aggregate02_grading_massfrac_17.
     */
    public void setCoarse_aggregate02_grading_massfrac_17(String coarse_aggregate02_grading_massfrac_17) {
        this.coarse_aggregate02_grading_massfrac_17 = coarse_aggregate02_grading_massfrac_17;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_18.
     */
    private String coarse_aggregate02_grading_massfrac_18;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_18.
     * @return Value of property coarse_aggregate02_grading_massfrac_18.
     */
    public String getCoarse_aggregate02_grading_massfrac_18() {
        return this.coarse_aggregate02_grading_massfrac_18;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_18.
     * @param coarse_aggregate02_grading_massfrac_18 New value of property coarse_aggregate02_grading_massfrac_18.
     */
    public void setCoarse_aggregate02_grading_massfrac_18(String coarse_aggregate02_grading_massfrac_18) {
        this.coarse_aggregate02_grading_massfrac_18 = coarse_aggregate02_grading_massfrac_18;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_19.
     */
    private String coarse_aggregate02_grading_massfrac_19;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_19.
     * @return Value of property coarse_aggregate02_grading_massfrac_19.
     */
    public String getCoarse_aggregate02_grading_massfrac_19() {
        return this.coarse_aggregate02_grading_massfrac_19;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_19.
     * @param coarse_aggregate02_grading_massfrac_19 New value of property coarse_aggregate02_grading_massfrac_19.
     */
    public void setCoarse_aggregate02_grading_massfrac_19(String coarse_aggregate02_grading_massfrac_19) {
        this.coarse_aggregate02_grading_massfrac_19 = coarse_aggregate02_grading_massfrac_19;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_20.
     */
    private String coarse_aggregate02_grading_massfrac_20;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_20.
     * @return Value of property coarse_aggregate02_grading_massfrac_20.
     */
    public String getCoarse_aggregate02_grading_massfrac_20() {
        return this.coarse_aggregate02_grading_massfrac_20;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_20.
     * @param coarse_aggregate02_grading_massfrac_20 New value of property coarse_aggregate02_grading_massfrac_20.
     */
    public void setCoarse_aggregate02_grading_massfrac_20(String coarse_aggregate02_grading_massfrac_20) {
        this.coarse_aggregate02_grading_massfrac_20 = coarse_aggregate02_grading_massfrac_20;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_21.
     */
    private String coarse_aggregate02_grading_massfrac_21;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_21.
     * @return Value of property coarse_aggregate02_grading_massfrac_21.
     */
    public String getCoarse_aggregate02_grading_massfrac_21() {
        return this.coarse_aggregate02_grading_massfrac_21;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_21.
     * @param coarse_aggregate02_grading_massfrac_21 New value of property coarse_aggregate02_grading_massfrac_21.
     */
    public void setCoarse_aggregate02_grading_massfrac_21(String coarse_aggregate02_grading_massfrac_21) {
        this.coarse_aggregate02_grading_massfrac_21 = coarse_aggregate02_grading_massfrac_21;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_massfrac_22.
     */
    private String coarse_aggregate02_grading_massfrac_22;

    /**
     * Getter for property coarse_aggregate02_grading_massfrac_22.
     * @return Value of property coarse_aggregate02_grading_massfrac_22.
     */
    public String getCoarse_aggregate02_grading_massfrac_22() {
        return this.coarse_aggregate02_grading_massfrac_22;
    }

    /**
     * Setter for property coarse_aggregate02_grading_massfrac_22.
     * @param coarse_aggregate02_grading_massfrac_22 New value of property coarse_aggregate02_grading_massfrac_22.
     */
    public void setCoarse_aggregate02_grading_massfrac_22(String coarse_aggregate02_grading_massfrac_22) {
        this.coarse_aggregate02_grading_massfrac_22 = coarse_aggregate02_grading_massfrac_22;
    }

    /**
     * Holds value of property coarse_aggregate02_grading_total_massfrac.
     */
    private String coarse_aggregate02_grading_total_massfrac;

    /**
     * Getter for property coarse_aggregate02_grading_total_massfrac.
     * @return Value of property coarse_aggregate02_grading_total_massfrac.
     */
    public String getCoarse_aggregate02_grading_total_massfrac() {
        return this.coarse_aggregate02_grading_total_massfrac;
    }

    /**
     * Setter for property coarse_aggregate02_grading_total_massfrac.
     * @param coarse_aggregate02_grading_total_massfrac New value of property coarse_aggregate02_grading_total_massfrac.
     */
    public void setCoarse_aggregate02_grading_total_massfrac(String coarse_aggregate02_grading_total_massfrac) {
        this.coarse_aggregate02_grading_total_massfrac = coarse_aggregate02_grading_total_massfrac;
    }

     /**
     * Holds value of property fine_aggregate02_grading_massfrac_0.
     */
    private String fine_aggregate02_grading_massfrac_0;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_0.
     * @return Value of property fine_aggregate02_grading_massfrac_0.
     */
    public String getFine_aggregate02_grading_massfrac_0() {
        return this.fine_aggregate02_grading_massfrac_0;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_0.
     * @param fine_aggregate02_grading_massfrac_0 New value of property fine_aggregate02_grading_massfrac_0.
     */
    public void setFine_aggregate02_grading_massfrac_0(String fine_aggregate02_grading_massfrac_0) {
        this.fine_aggregate02_grading_massfrac_0 = fine_aggregate02_grading_massfrac_0;
    }
    /**
     * Holds value of property fine_aggregate02_grading_massfrac_1.
     */
    private String fine_aggregate02_grading_massfrac_1;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_1.
     * @return Value of property fine_aggregate02_grading_massfrac_1.
     */
    public String getFine_aggregate02_grading_massfrac_1() {
        return this.fine_aggregate02_grading_massfrac_1;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_1.
     * @param fine_aggregate02_grading_massfrac_1 New value of property fine_aggregate02_grading_massfrac_1.
     */
    public void setFine_aggregate02_grading_massfrac_1(String fine_aggregate02_grading_massfrac_1) {
        this.fine_aggregate02_grading_massfrac_1 = fine_aggregate02_grading_massfrac_1;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_2.
     */
    private String fine_aggregate02_grading_massfrac_2;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_2.
     * @return Value of property fine_aggregate02_grading_massfrac_2.
     */
    public String getFine_aggregate02_grading_massfrac_2() {
        return this.fine_aggregate02_grading_massfrac_2;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_2.
     * @param fine_aggregate02_grading_massfrac_2 New value of property fine_aggregate02_grading_massfrac_2.
     */
    public void setFine_aggregate02_grading_massfrac_2(String fine_aggregate02_grading_massfrac_2) {
        this.fine_aggregate02_grading_massfrac_2 = fine_aggregate02_grading_massfrac_2;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_3.
     */
    private String fine_aggregate02_grading_massfrac_3;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_3.
     * @return Value of property fine_aggregate02_grading_massfrac_3.
     */
    public String getFine_aggregate02_grading_massfrac_3() {
        return this.fine_aggregate02_grading_massfrac_3;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_3.
     * @param fine_aggregate02_grading_massfrac_3 New value of property fine_aggregate02_grading_massfrac_3.
     */
    public void setFine_aggregate02_grading_massfrac_3(String fine_aggregate02_grading_massfrac_3) {
        this.fine_aggregate02_grading_massfrac_3 = fine_aggregate02_grading_massfrac_3;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_4.
     */
    private String fine_aggregate02_grading_massfrac_4;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_4.
     * @return Value of property fine_aggregate02_grading_massfrac_4.
     */
    public String getFine_aggregate02_grading_massfrac_4() {
        return this.fine_aggregate02_grading_massfrac_4;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_4.
     * @param fine_aggregate02_grading_massfrac_4 New value of property fine_aggregate02_grading_massfrac_4.
     */
    public void setFine_aggregate02_grading_massfrac_4(String fine_aggregate02_grading_massfrac_4) {
        this.fine_aggregate02_grading_massfrac_4 = fine_aggregate02_grading_massfrac_4;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_5.
     */
    private String fine_aggregate02_grading_massfrac_5;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_5.
     * @return Value of property fine_aggregate02_grading_massfrac_5.
     */
    public String getFine_aggregate02_grading_massfrac_5() {
        return this.fine_aggregate02_grading_massfrac_5;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_5.
     * @param fine_aggregate02_grading_massfrac_5 New value of property fine_aggregate02_grading_massfrac_5.
     */
    public void setFine_aggregate02_grading_massfrac_5(String fine_aggregate02_grading_massfrac_5) {
        this.fine_aggregate02_grading_massfrac_5 = fine_aggregate02_grading_massfrac_5;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_6.
     */
    private String fine_aggregate02_grading_massfrac_6;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_6.
     * @return Value of property fine_aggregate02_grading_massfrac_6.
     */
    public String getFine_aggregate02_grading_massfrac_6() {
        return this.fine_aggregate02_grading_massfrac_6;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_6.
     * @param fine_aggregate02_grading_massfrac_6 New value of property fine_aggregate02_grading_massfrac_6.
     */
    public void setFine_aggregate02_grading_massfrac_6(String fine_aggregate02_grading_massfrac_6) {
        this.fine_aggregate02_grading_massfrac_6 = fine_aggregate02_grading_massfrac_6;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_7.
     */
    private String fine_aggregate02_grading_massfrac_7;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_7.
     * @return Value of property fine_aggregate02_grading_massfrac_7.
     */
    public String getFine_aggregate02_grading_massfrac_7() {
        return this.fine_aggregate02_grading_massfrac_7;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_7.
     * @param fine_aggregate02_grading_massfrac_7 New value of property fine_aggregate02_grading_massfrac_7.
     */
    public void setFine_aggregate02_grading_massfrac_7(String fine_aggregate02_grading_massfrac_7) {
        this.fine_aggregate02_grading_massfrac_7 = fine_aggregate02_grading_massfrac_7;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_8.
     */
    private String fine_aggregate02_grading_massfrac_8;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_8.
     * @return Value of property fine_aggregate02_grading_massfrac_8.
     */
    public String getFine_aggregate02_grading_massfrac_8() {
        return this.fine_aggregate02_grading_massfrac_8;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_8.
     * @param fine_aggregate02_grading_massfrac_8 New value of property fine_aggregate02_grading_massfrac_8.
     */
    public void setFine_aggregate02_grading_massfrac_8(String fine_aggregate02_grading_massfrac_8) {
        this.fine_aggregate02_grading_massfrac_8 = fine_aggregate02_grading_massfrac_8;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_9.
     */
    private String fine_aggregate02_grading_massfrac_9;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_9.
     * @return Value of property fine_aggregate02_grading_massfrac_9.
     */
    public String getFine_aggregate02_grading_massfrac_9() {
        return this.fine_aggregate02_grading_massfrac_9;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_9.
     * @param fine_aggregate02_grading_massfrac_9 New value of property fine_aggregate02_grading_massfrac_9.
     */
    public void setFine_aggregate02_grading_massfrac_9(String fine_aggregate02_grading_massfrac_9) {
        this.fine_aggregate02_grading_massfrac_9 = fine_aggregate02_grading_massfrac_9;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_10.
     */
    private String fine_aggregate02_grading_massfrac_10;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_10.
     * @return Value of property fine_aggregate02_grading_massfrac_10.
     */
    public String getFine_aggregate02_grading_massfrac_10() {
        return this.fine_aggregate02_grading_massfrac_10;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_10.
     * @param fine_aggregate02_grading_massfrac_10 New value of property fine_aggregate02_grading_massfrac_10.
     */
    public void setFine_aggregate02_grading_massfrac_10(String fine_aggregate02_grading_massfrac_10) {
        this.fine_aggregate02_grading_massfrac_10 = fine_aggregate02_grading_massfrac_10;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_11.
     */
    private String fine_aggregate02_grading_massfrac_11;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_11.
     * @return Value of property fine_aggregate02_grading_massfrac_11.
     */
    public String getFine_aggregate02_grading_massfrac_11() {
        return this.fine_aggregate02_grading_massfrac_11;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_11.
     * @param fine_aggregate02_grading_massfrac_11 New value of property fine_aggregate02_grading_massfrac_11.
     */
    public void setFine_aggregate02_grading_massfrac_11(String fine_aggregate02_grading_massfrac_11) {
        this.fine_aggregate02_grading_massfrac_11 = fine_aggregate02_grading_massfrac_11;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_12.
     */
    private String fine_aggregate02_grading_massfrac_12;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_12.
     * @return Value of property fine_aggregate02_grading_massfrac_12.
     */
    public String getFine_aggregate02_grading_massfrac_12() {
        return this.fine_aggregate02_grading_massfrac_12;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_12.
     * @param fine_aggregate02_grading_massfrac_12 New value of property fine_aggregate02_grading_massfrac_12.
     */
    public void setFine_aggregate02_grading_massfrac_12(String fine_aggregate02_grading_massfrac_12) {
        this.fine_aggregate02_grading_massfrac_12 = fine_aggregate02_grading_massfrac_12;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_13.
     */
    private String fine_aggregate02_grading_massfrac_13;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_13.
     * @return Value of property fine_aggregate02_grading_massfrac_13.
     */
    public String getFine_aggregate02_grading_massfrac_13() {
        return this.fine_aggregate02_grading_massfrac_13;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_13.
     * @param fine_aggregate02_grading_massfrac_13 New value of property fine_aggregate02_grading_massfrac_13.
     */
    public void setFine_aggregate02_grading_massfrac_13(String fine_aggregate02_grading_massfrac_13) {
        this.fine_aggregate02_grading_massfrac_13 = fine_aggregate02_grading_massfrac_13;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_14.
     */
    private String fine_aggregate02_grading_massfrac_14;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_4.
     * @return Value of property fine_aggregate02_grading_massfrac_4.
     */
    public String getFine_aggregate02_grading_massfrac_14() {
        return this.fine_aggregate02_grading_massfrac_14;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_14.
     * @param fine_aggregate02_grading_massfrac_14 New value of property fine_aggregate02_grading_massfrac_14.
     */
    public void setFine_aggregate02_grading_massfrac_14(String fine_aggregate02_grading_massfrac_14) {
        this.fine_aggregate02_grading_massfrac_14 = fine_aggregate02_grading_massfrac_14;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_15.
     */
    private String fine_aggregate02_grading_massfrac_15;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_15.
     * @return Value of property fine_aggregate02_grading_massfrac_15.
     */
    public String getFine_aggregate02_grading_massfrac_15() {
        return this.fine_aggregate02_grading_massfrac_15;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_15.
     * @param fine_aggregate02_grading_massfrac_15 New value of property fine_aggregate02_grading_massfrac_15.
     */
    public void setFine_aggregate02_grading_massfrac_15(String fine_aggregate02_grading_massfrac_15) {
        this.fine_aggregate02_grading_massfrac_15 = fine_aggregate02_grading_massfrac_15;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_16.
     */
    private String fine_aggregate02_grading_massfrac_16;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_16.
     * @return Value of property fine_aggregate02_grading_massfrac_16.
     */
    public String getFine_aggregate02_grading_massfrac_16() {
        return this.fine_aggregate02_grading_massfrac_16;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_16.
     * @param fine_aggregate02_grading_massfrac_16 New value of property fine_aggregate02_grading_massfrac_16.
     */
    public void setFine_aggregate02_grading_massfrac_16(String fine_aggregate02_grading_massfrac_16) {
        this.fine_aggregate02_grading_massfrac_16 = fine_aggregate02_grading_massfrac_16;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_17.
     */
    private String fine_aggregate02_grading_massfrac_17;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_17.
     * @return Value of property fine_aggregate02_grading_massfrac_17.
     */
    public String getFine_aggregate02_grading_massfrac_17() {
        return this.fine_aggregate02_grading_massfrac_17;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_17.
     * @param fine_aggregate02_grading_massfrac_17 New value of property fine_aggregate02_grading_massfrac_17.
     */
    public void setFine_aggregate02_grading_massfrac_17(String fine_aggregate02_grading_massfrac_17) {
        this.fine_aggregate02_grading_massfrac_17 = fine_aggregate02_grading_massfrac_17;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_18.
     */
    private String fine_aggregate02_grading_massfrac_18;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_18.
     * @return Value of property fine_aggregate02_grading_massfrac_18.
     */
    public String getFine_aggregate02_grading_massfrac_18() {
        return this.fine_aggregate02_grading_massfrac_18;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_18.
     * @param fine_aggregate02_grading_massfrac_18 New value of property fine_aggregate02_grading_massfrac_18.
     */
    public void setFine_aggregate02_grading_massfrac_18(String fine_aggregate02_grading_massfrac_18) {
        this.fine_aggregate02_grading_massfrac_18 = fine_aggregate02_grading_massfrac_18;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_19.
     */
    private String fine_aggregate02_grading_massfrac_19;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_19.
     * @return Value of property fine_aggregate02_grading_massfrac_19.
     */
    public String getFine_aggregate02_grading_massfrac_19() {
        return this.fine_aggregate02_grading_massfrac_19;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_19.
     * @param fine_aggregate02_grading_massfrac_19 New value of property fine_aggregate02_grading_massfrac_19.
     */
    public void setFine_aggregate02_grading_massfrac_19(String fine_aggregate02_grading_massfrac_19) {
        this.fine_aggregate02_grading_massfrac_19 = fine_aggregate02_grading_massfrac_19;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_20.
     */
    private String fine_aggregate02_grading_massfrac_20;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_20.
     * @return Value of property fine_aggregate02_grading_massfrac_20.
     */
    public String getFine_aggregate02_grading_massfrac_20() {
        return this.fine_aggregate02_grading_massfrac_20;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_20.
     * @param fine_aggregate02_grading_massfrac_20 New value of property fine_aggregate02_grading_massfrac_20.
     */
    public void setFine_aggregate02_grading_massfrac_20(String fine_aggregate02_grading_massfrac_20) {
        this.fine_aggregate02_grading_massfrac_20 = fine_aggregate02_grading_massfrac_20;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_21.
     */
    private String fine_aggregate02_grading_massfrac_21;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_21.
     * @return Value of property fine_aggregate02_grading_massfrac_21.
     */
    public String getFine_aggregate02_grading_massfrac_21() {
        return this.fine_aggregate02_grading_massfrac_21;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_21.
     * @param fine_aggregate02_grading_massfrac_21 New value of property fine_aggregate02_grading_massfrac_21.
     */
    public void setFine_aggregate02_grading_massfrac_21(String fine_aggregate02_grading_massfrac_21) {
        this.fine_aggregate02_grading_massfrac_21 = fine_aggregate02_grading_massfrac_21;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_22.
     */
    private String fine_aggregate02_grading_massfrac_22;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_22.
     * @return Value of property fine_aggregate02_grading_massfrac_22.
     */
    public String getFine_aggregate02_grading_massfrac_22() {
        return this.fine_aggregate02_grading_massfrac_22;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_22.
     * @param fine_aggregate02_grading_massfrac_22 New value of property fine_aggregate02_grading_massfrac_22.
     */
    public void setFine_aggregate02_grading_massfrac_22(String fine_aggregate02_grading_massfrac_22) {
        this.fine_aggregate02_grading_massfrac_22 = fine_aggregate02_grading_massfrac_22;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_23.
     */
    private String fine_aggregate02_grading_massfrac_23;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_23.
     * @return Value of property fine_aggregate02_grading_massfrac_23.
     */
    public String getFine_aggregate02_grading_massfrac_23() {
        return this.fine_aggregate02_grading_massfrac_23;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_23.
     * @param fine_aggregate02_grading_massfrac_23 New value of property fine_aggregate02_grading_massfrac_23.
     */
    public void setFine_aggregate02_grading_massfrac_23(String fine_aggregate02_grading_massfrac_23) {
        this.fine_aggregate02_grading_massfrac_23 = fine_aggregate02_grading_massfrac_23;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_24.
     */
    private String fine_aggregate02_grading_massfrac_24;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_24.
     * @return Value of property fine_aggregate02_grading_massfrac_24.
     */
    public String getFine_aggregate02_grading_massfrac_24() {
        return this.fine_aggregate02_grading_massfrac_24;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_24.
     * @param fine_aggregate02_grading_massfrac_24 New value of property fine_aggregate02_grading_massfrac_24.
     */
    public void setFine_aggregate02_grading_massfrac_24(String fine_aggregate02_grading_massfrac_24) {
        this.fine_aggregate02_grading_massfrac_24 = fine_aggregate02_grading_massfrac_24;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_25.
     */
    private String fine_aggregate02_grading_massfrac_25;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_25.
     * @return Value of property fine_aggregate02_grading_massfrac_25.
     */
    public String getFine_aggregate02_grading_massfrac_25() {
        return this.fine_aggregate02_grading_massfrac_25;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_25.
     * @param fine_aggregate02_grading_massfrac_25 New value of property fine_aggregate02_grading_massfrac_25.
     */
    public void setFine_aggregate02_grading_massfrac_25(String fine_aggregate02_grading_massfrac_25) {
        this.fine_aggregate02_grading_massfrac_25 = fine_aggregate02_grading_massfrac_25;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_26.
     */
    private String fine_aggregate02_grading_massfrac_26;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_26.
     * @return Value of property fine_aggregate02_grading_massfrac_26.
     */
    public String getFine_aggregate02_grading_massfrac_26() {
        return this.fine_aggregate02_grading_massfrac_26;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_26.
     * @param fine_aggregate02_grading_massfrac_26 New value of property fine_aggregate02_grading_massfrac_26.
     */
    public void setFine_aggregate02_grading_massfrac_26(String fine_aggregate02_grading_massfrac_26) {
        this.fine_aggregate02_grading_massfrac_26 = fine_aggregate02_grading_massfrac_26;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_27.
     */
    private String fine_aggregate02_grading_massfrac_27;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_27.
     * @return Value of property fine_aggregate02_grading_massfrac_27.
     */
    public String getFine_aggregate02_grading_massfrac_27() {
        return this.fine_aggregate02_grading_massfrac_27;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_27.
     * @param fine_aggregate02_grading_massfrac_27 New value of property fine_aggregate02_grading_massfrac_27.
     */
    public void setFine_aggregate02_grading_massfrac_27(String fine_aggregate02_grading_massfrac_27) {
        this.fine_aggregate02_grading_massfrac_27 = fine_aggregate02_grading_massfrac_27;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_28.
     */
    private String fine_aggregate02_grading_massfrac_28;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_28.
     * @return Value of property fine_aggregate02_grading_massfrac_28.
     */
    public String getFine_aggregate02_grading_massfrac_28() {
        return this.fine_aggregate02_grading_massfrac_28;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_28.
     * @param fine_aggregate02_grading_massfrac_28 New value of property fine_aggregate02_grading_massfrac_28.
     */
    public void setFine_aggregate02_grading_massfrac_28(String fine_aggregate02_grading_massfrac_28) {
        this.fine_aggregate02_grading_massfrac_28 = fine_aggregate02_grading_massfrac_28;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_29.
     */
    private String fine_aggregate02_grading_massfrac_29;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_29.
     * @return Value of property fine_aggregate02_grading_massfrac_29.
     */
    public String getFine_aggregate02_grading_massfrac_29() {
        return this.fine_aggregate02_grading_massfrac_29;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_29.
     * @param fine_aggregate02_grading_massfrac_29 New value of property fine_aggregate02_grading_massfrac_29.
     */
    public void setFine_aggregate02_grading_massfrac_29(String fine_aggregate02_grading_massfrac_29) {
        this.fine_aggregate02_grading_massfrac_29 = fine_aggregate02_grading_massfrac_29;
    }

    /**
     * Holds value of property fine_aggregate02_grading_massfrac_30.
     */
    private String fine_aggregate02_grading_massfrac_30;

    /**
     * Getter for property fine_aggregate02_grading_massfrac_30.
     * @return Value of property fine_aggregate02_grading_massfrac_30.
     */
    public String getFine_aggregate02_grading_massfrac_30() {
        return this.fine_aggregate02_grading_massfrac_30;
    }

    /**
     * Setter for property fine_aggregate02_grading_massfrac_30.
     * @param fine_aggregate02_grading_massfrac_30 New value of property fine_aggregate02_grading_massfrac_30.
     */
    public void setFine_aggregate02_grading_massfrac_30(String fine_aggregate02_grading_massfrac_30) {
        this.fine_aggregate02_grading_massfrac_30 = fine_aggregate02_grading_massfrac_30;
    }

    /**
     * Holds value of property cement_massfrac.
     */
    private String cement_massfrac;
    
    /**
     * Getter for property cement_massfrac.
     * @return Value of property cement_massfrac.
     */
    public String getCement_massfrac() {
        return this.cement_massfrac;
    }
    
    /**
     * Setter for property cement_massfrac.
     * @param cement_massfrac New value of property cement_massfrac.
     */
    public void setCement_massfrac(String cement_massfrac) {
        this.cement_massfrac = cement_massfrac;
    }
    
    /**
     * Holds value of property cement_volfrac.
     */
    private String cement_volfrac;
    
    /**
     * Getter for property cement_volfrac.
     * @return Value of property cement_volfrac.
     */
    public String getCement_volfrac() {
        return this.cement_volfrac;
    }
    
    /**
     * Setter for property cement_volfrac.
     * @param cement_volfrac New value of property cement_volfrac.
     */
    public void setCement_volfrac(String cement_volfrac) {
        this.cement_volfrac = cement_volfrac;
    }
    
    /**
     * Holds value of property coarse_aggregate01_grading.
     */
    private String coarse_aggregate01_grading;
    
    /**
     * Getter for property coarse_aggregate01_grading.
     * @return Value of property coarse_aggregate01_grading.
     */
    public String getCoarse_aggregate01_grading() {
        return this.coarse_aggregate01_grading;
    }
    
    /**
     * Setter for property coarse_aggregate01_grading.
     * @param coarse_aggregate01_grading New value of property coarse_aggregate01_grading.
     */
    public void setCoarse_aggregate01_grading(String coarse_aggregate01_grading) {
        this.coarse_aggregate01_grading = coarse_aggregate01_grading;
    }
    
    /**
     * Holds value of property fine_aggregate01_grading.
     */
    private String fine_aggregate01_grading;
    
    /**
     * Getter for property fine_aggregate01_grading.
     * @return Value of property fine_aggregate01_grading.
     */
    public String getFine_aggregate01_grading() {
        return this.fine_aggregate01_grading;
    }
    
    /**
     * Setter for property fine_aggregate01_grading.
     * @param fine_aggregate01_grading New value of property fine_aggregate01_grading.
     */
    public void setFine_aggregate01_grading(String fine_aggregate01_grading) {
        this.fine_aggregate01_grading = fine_aggregate01_grading;
    }
    
    /**
     * Holds value of property new_fine_aggregate01_grading_name.
     */
    private String new_fine_aggregate01_grading_name;
    
    /**
     * Getter for property new_fine_aggregate01_grading_name.
     * @return Value of property new_fine_aggregate01_grading_name.
     */
    public String getNew_fine_aggregate01_grading_name() {
        return this.new_fine_aggregate01_grading_name;
    }
    
    /**
     * Setter for property new_fine_aggregate01_grading_name.
     * @param new_fine_aggregate01_grading_name New value of property new_fine_aggregate01_grading_name.
     */
    public void setNew_fine_aggregate01_grading_name(String new_fine_aggregate01_grading_name) {
        this.new_fine_aggregate01_grading_name = new_fine_aggregate01_grading_name;
    }
    
    /**
     * Holds value of property new_coarse_aggregate01_grading_name.
     */
    private String new_coarse_aggregate01_grading_name;
    
    /**
     * Getter for property new_coarse_aggregate01_grading_name.
     * @return Value of property new_coarse_aggregate01_grading_name.
     */
    public String getNew_coarse_aggregate01_grading_name() {
        return this.new_coarse_aggregate01_grading_name;
    }
    
    /**
     * Setter for property new_coarse_aggregate01_grading_name.
     * @param new_coarse_aggregate01_grading_name New value of property new_coarse_aggregate01_grading_name.
     */
    public void setNew_coarse_aggregate01_grading_name(String new_coarse_aggregate01_grading_name) {
        this.new_coarse_aggregate01_grading_name = new_coarse_aggregate01_grading_name;
    }

     /**
     * Holds value of property coarse_aggregate02_grading.
     */
    private String coarse_aggregate02_grading;

    /**
     * Getter for property coarse_aggregate02_grading.
     * @return Value of property coarse_aggregate02_grading.
     */
    public String getCoarse_aggregate02_grading() {
        return this.coarse_aggregate02_grading;
    }

    /**
     * Setter for property coarse_aggregate02_grading.
     * @param coarse_aggregate02_grading New value of property coarse_aggregate02_grading.
     */
    public void setCoarse_aggregate02_grading(String coarse_aggregate02_grading) {
        this.coarse_aggregate02_grading = coarse_aggregate02_grading;
    }

    /**
     * Holds value of property fine_aggregate02_grading.
     */
    private String fine_aggregate02_grading;

    /**
     * Getter for property fine_aggregate02_grading.
     * @return Value of property fine_aggregate02_grading.
     */
    public String getFine_aggregate02_grading() {
        return this.fine_aggregate02_grading;
    }

    /**
     * Setter for property fine_aggregate02_grading.
     * @param fine_aggregate02_grading New value of property fine_aggregate02_grading.
     */
    public void setFine_aggregate02_grading(String fine_aggregate02_grading) {
        this.fine_aggregate02_grading = fine_aggregate02_grading;
    }

    /**
     * Holds value of property new_fine_aggregate02_grading_name.
     */
    private String new_fine_aggregate02_grading_name;

    /**
     * Getter for property new_fine_aggregate02_grading_name.
     * @return Value of property new_fine_aggregate02_grading_name.
     */
    public String getNew_fine_aggregate02_grading_name() {
        return this.new_fine_aggregate02_grading_name;
    }

    /**
     * Setter for property new_fine_aggregate02_grading_name.
     * @param new_fine_aggregate02_grading_name New value of property new_fine_aggregate02_grading_name.
     */
    public void setNew_fine_aggregate02_grading_name(String new_fine_aggregate02_grading_name) {
        this.new_fine_aggregate02_grading_name = new_fine_aggregate02_grading_name;
    }

    /**
     * Holds value of property new_coarse_aggregate02_grading_name.
     */
    private String new_coarse_aggregate02_grading_name;

    /**
     * Getter for property new_coarse_aggregate02_grading_name.
     * @return Value of property new_coarse_aggregate02_grading_name.
     */
    public String getNew_coarse_aggregate02_grading_name() {
        return this.new_coarse_aggregate02_grading_name;
    }

    /**
     * Setter for property new_coarse_aggregate02_grading_name.
     * @param new_coarse_aggregate02_grading_name New value of property new_coarse_aggregate02_grading_name.
     */
    public void setNew_coarse_aggregate02_grading_name(String new_coarse_aggregate02_grading_name) {
        this.new_coarse_aggregate02_grading_name = new_coarse_aggregate02_grading_name;
    }

    public void saveNewCoarse01Grading() throws SQLDuplicatedKeyException, SQLArgumentException, SQLException, ParseException {
        Grading grading = new Grading();
        grading.setGrading(coarse_aggregate01_grading.getBytes());
        double cagmd = Double.parseDouble(coarse_aggregate01_grading_max_diam);
        grading.setMax_diameter(cagmd);
        grading.setName(new_coarse_aggregate01_grading_name);
        grading.setType(1);
        grading.save();
        coarse_aggregate01_grading_name = new_coarse_aggregate01_grading_name;
    }
    
    public void saveNewFine01Grading() throws SQLDuplicatedKeyException, SQLArgumentException, SQLException, ParseException {
        Grading grading = new Grading();
        grading.setGrading(fine_aggregate01_grading.getBytes());
        double fagmd = Double.parseDouble(fine_aggregate01_grading_max_diam);
        grading.setMax_diameter(fagmd);
        grading.setName(new_fine_aggregate01_grading_name);
        grading.setType(0);
        grading.save();
        fine_aggregate01_grading_name = new_fine_aggregate01_grading_name;
    }
    
    public boolean updateCoarseAggregate01Grading() throws SQLArgumentException, SQLException, ParseException {
        String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
        String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
        String fine01GradingString,fine02GradingString;
        if (isAdd_fine_aggregate01()) {
            fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
            fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
            if (!this.checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString,fine01GradingString,fine02GradingString)) {
                this.setCoarse_aggregate01_grading_name(this.previousCoarse01Grading);
                coarse_aggregate01_grading = CementDatabase.getGrading(coarse_aggregate01_grading_name);
                this.previousCoarse01Grading = coarse_aggregate01_grading_name;
                return false;
            }
        } else if (!this.checkCoarseAggregate01Grading(coarse01GradingString)) {
            this.setCoarse_aggregate01_grading_name(this.previousCoarse01Grading);
            coarse_aggregate01_grading = CementDatabase.getGrading(coarse_aggregate01_grading_name);
            this.previousCoarse01Grading = coarse_aggregate01_grading_name;
            return false;
        }

        coarse_aggregate01_grading = coarse01GradingString;
        String[][] grading = getGradingFromString(coarse_aggregate01_grading);
        this.setCoarse_aggregate01_grading_massfrac_0(grading[2][0]);
        this.setCoarse_aggregate01_grading_massfrac_1(grading[2][1]);
        this.setCoarse_aggregate01_grading_massfrac_2(grading[2][2]);
        this.setCoarse_aggregate01_grading_massfrac_3(grading[2][3]);
        this.setCoarse_aggregate01_grading_massfrac_4(grading[2][4]);
        this.setCoarse_aggregate01_grading_massfrac_5(grading[2][5]);
        this.setCoarse_aggregate01_grading_massfrac_6(grading[2][6]);
        this.setCoarse_aggregate01_grading_massfrac_7(grading[2][7]);
        this.setCoarse_aggregate01_grading_massfrac_8(grading[2][8]);
        this.setCoarse_aggregate01_grading_massfrac_9(grading[2][9]);
        this.setCoarse_aggregate01_grading_massfrac_10(grading[2][10]);
        this.setCoarse_aggregate01_grading_massfrac_11(grading[2][11]);
        this.setCoarse_aggregate01_grading_massfrac_12(grading[2][12]);
        this.setCoarse_aggregate01_grading_massfrac_13(grading[2][13]);
        this.setCoarse_aggregate01_grading_massfrac_14(grading[2][14]);
        this.setCoarse_aggregate01_grading_massfrac_15(grading[2][15]);
        this.setCoarse_aggregate01_grading_massfrac_16(grading[2][16]);
        this.setCoarse_aggregate01_grading_massfrac_17(grading[2][17]);
        this.setCoarse_aggregate01_grading_massfrac_18(grading[2][18]);
        this.setCoarse_aggregate01_grading_massfrac_19(grading[2][19]);
        this.setCoarse_aggregate01_grading_massfrac_20(grading[2][20]);
        this.setCoarse_aggregate01_grading_massfrac_21(grading[2][21]);
        this.setCoarse_aggregate01_grading_massfrac_22(grading[2][22]);

        double sum = 0.0;
        for (int i = 0; i < grading[2].length; i++) {
            if (Double.parseDouble(grading[2][i]) > 0.0) {
                sum += Double.parseDouble(grading[2][i]);
            }
        }

        this.setCoarse_aggregate01_grading_total_massfrac(String.valueOf(sum));
        coarse_aggregate01_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(coarse_aggregate01_grading_name));
        this.setCoarse_aggregate01_grading_max_diam(coarse_aggregate01_grading_max_diam);
        return true;
    }
    
    public boolean updateFineAggregate01Grading() throws SQLArgumentException, SQLException, ParseException {
        String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
        String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
        String coarse01GradingString,coarse02GradingString;
        if (isAdd_coarse_aggregate01()) {
            coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
            coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
            if (!this.checkAllAggregateGradingsAtOnce(coarse01GradingString, coarse02GradingString, fine01GradingString, fine02GradingString)) {
                this.setFine_aggregate01_grading_name(this.previousFine01Grading);
                fine_aggregate01_grading = CementDatabase.getGrading(fine_aggregate01_grading_name);
                this.previousFine01Grading = fine_aggregate01_grading_name;
                return false;
            }
        } else if (!this.checkFineAggregate01Grading(fine01GradingString)) {
            this.setFine_aggregate01_grading_name(this.previousFine01Grading);
            fine_aggregate01_grading = CementDatabase.getGrading(fine_aggregate01_grading_name);
            this.previousFine01Grading = fine_aggregate01_grading_name;
            return false;
        }

        fine_aggregate01_grading = fine01GradingString;
        String[][] grading = getGradingFromString(fine_aggregate01_grading);
        this.setFine_aggregate01_grading_massfrac_0(grading[2][0]);
        this.setFine_aggregate01_grading_massfrac_1(grading[2][1]);
        this.setFine_aggregate01_grading_massfrac_2(grading[2][2]);
        this.setFine_aggregate01_grading_massfrac_3(grading[2][3]);
        this.setFine_aggregate01_grading_massfrac_4(grading[2][4]);
        this.setFine_aggregate01_grading_massfrac_5(grading[2][5]);
        this.setFine_aggregate01_grading_massfrac_6(grading[2][6]);
        this.setFine_aggregate01_grading_massfrac_7(grading[2][7]);
        this.setFine_aggregate01_grading_massfrac_8(grading[2][8]);
        this.setFine_aggregate01_grading_massfrac_9(grading[2][9]);
        this.setFine_aggregate01_grading_massfrac_10(grading[2][10]);
        this.setFine_aggregate01_grading_massfrac_11(grading[2][11]);
        this.setFine_aggregate01_grading_massfrac_12(grading[2][12]);
        this.setFine_aggregate01_grading_massfrac_13(grading[2][13]);
        this.setFine_aggregate01_grading_massfrac_14(grading[2][14]);
        this.setFine_aggregate01_grading_massfrac_15(grading[2][15]);
        this.setFine_aggregate01_grading_massfrac_16(grading[2][16]);
        this.setFine_aggregate01_grading_massfrac_17(grading[2][17]);
        this.setFine_aggregate01_grading_massfrac_18(grading[2][18]);
        this.setFine_aggregate01_grading_massfrac_19(grading[2][19]);
        this.setFine_aggregate01_grading_massfrac_20(grading[2][20]);
        this.setFine_aggregate01_grading_massfrac_21(grading[2][21]);
        this.setFine_aggregate01_grading_massfrac_22(grading[2][22]);
        this.setFine_aggregate01_grading_massfrac_23(grading[2][23]);
        this.setFine_aggregate01_grading_massfrac_24(grading[2][24]);
        this.setFine_aggregate01_grading_massfrac_25(grading[2][25]);
        this.setFine_aggregate01_grading_massfrac_26(grading[2][26]);
        this.setFine_aggregate01_grading_massfrac_27(grading[2][27]);
        this.setFine_aggregate01_grading_massfrac_28(grading[2][28]);
        this.setFine_aggregate01_grading_massfrac_29(grading[2][29]);
        this.setFine_aggregate01_grading_massfrac_30(grading[2][30]);

        fine_aggregate01_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(fine_aggregate01_grading_name));
        this.setFine_aggregate01_grading_max_diam(fine_aggregate01_grading_max_diam);
        return true;
    }
    
    public boolean checkCoarseAggregate01Grading() throws SQLArgumentException, SQLException, ParseException {
        String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
        String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
        if (isAdd_fine_aggregate01()) {
            String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
            String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
            return checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString,fine01GradingString,fine02GradingString);
        } else {
            return checkCoarseAggregate01Grading(coarse01GradingString);
        }
    }
    
    public boolean checkCoarseAggregate01Grading(String coarse01GradingString) throws ParseException {
        // check if the biggest present sieve isn't too big for the system size and if the smallest one is not too small
        String[][] coarse01Grading = getGradingFromString(coarse01GradingString);
        double biggestPresentSieveDiameter = 0.0;
        double smallestPresentSieveDiameter = 0.0;
        boolean biggestPresentSieveFound = false;
        double cG2i = 0.0;
        for (int i = 0; i < coarse01Grading[2].length; i++) {
            cG2i = Double.parseDouble(coarse01Grading[2][i]);

            if (cG2i > 0.0) {
                if (biggestPresentSieveFound == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter = Double.parseDouble(this.getFine_aggregate01_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter = Double.parseDouble(coarse01Grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound = true;
                smallestPresentSieveDiameter = Double.parseDouble(coarse01Grading[1][i]);
            }
        }
        double res = Double.parseDouble(this.getConcrete_resolution());

        double newRes = smallestPresentSieveDiameter/Constants.RESOLUTION_SAFETY_COEFFICIENT;
        newRes *= 100.00;
        double roundedNewRes = Math.round(newRes);
        roundedNewRes /= 100.00;

        double xDim = 0.0;
        double minDim = 0.0;
        xDim = Double.parseDouble(this.getConcrete_x_dim());

        minDim = xDim;
        double yDim = Double.parseDouble(this.getConcrete_y_dim());
        if (yDim < minDim) {
            minDim = yDim;
        }
        double zDim = Double.parseDouble(this.getConcrete_z_dim());
        if (zDim < minDim) {
                minDim = zDim;
        }

        // double maxSize = Constants.SIZE_SAFETY_COEFFICIENT * minDim;
        // if (biggestPresentSieveDiameter > maxSize) {
            minDim = (double)(biggestPresentSieveDiameter/(Constants.SIZE_SAFETY_COEFFICIENT));
            int resMultiples = (int) (minDim/roundedNewRes + 0.5);
            minDim = roundedNewRes * resMultiples;

            minDim *= 100.00;
            double roundedMinDim =  Math.round(minDim);
            roundedMinDim /= 100.0;
            // DecimalFormat TwoDP = new DecimalFormat("#0.00");
            // String formattedMinDim = TwoDP.format(roundedMinDim);
            // String formattedNewRes = TwoDP.format(roundedNewRes);
            this.setConcrete_x_dim(Double.toString(roundedMinDim));
            this.setConcrete_y_dim(Double.toString(roundedMinDim));
            this.setConcrete_z_dim(Double.toString(roundedMinDim));
        // }

        // double minSize = Constants.RESOLUTION_SAFETY_COEFFICIENT * Double.parseDouble(this.getConcrete_resolution());
        // if (smallestPresentSieveDiameter < minSize) {
            this.setConcrete_resolution(Double.toString(roundedNewRes));
        // }
        
        return true;
    }

    public void saveNewCoarse02Grading() throws SQLDuplicatedKeyException, SQLArgumentException, SQLException, ParseException {
        Grading grading = new Grading();
        grading.setGrading(coarse_aggregate02_grading.getBytes());
        double cagmd = Double.parseDouble(coarse_aggregate02_grading_max_diam);
        grading.setMax_diameter(cagmd);
        grading.setName(new_coarse_aggregate02_grading_name);
        grading.setType(1);
        grading.save();
        coarse_aggregate02_grading_name = new_coarse_aggregate02_grading_name;
    }

    public void saveNewFine02Grading() throws SQLDuplicatedKeyException, SQLArgumentException, SQLException, ParseException {
        Grading grading = new Grading();
        grading.setGrading(fine_aggregate02_grading.getBytes());
        double fagmd = Double.parseDouble(fine_aggregate02_grading_max_diam);
        grading.setMax_diameter(fagmd);
        grading.setName(new_fine_aggregate02_grading_name);
        grading.setType(0);
        grading.save();
        fine_aggregate02_grading_name = new_fine_aggregate02_grading_name;
    }

    public boolean updateCoarseAggregate02Grading() throws SQLArgumentException, SQLException, ParseException {
        String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
        String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
        String fine01GradingString,fine02GradingString;
        if (isAdd_fine_aggregate01()) {
            fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
            fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
            if (!this.checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString,fine01GradingString,fine02GradingString)) {
                this.setCoarse_aggregate02_grading_name(this.previousCoarse02Grading);
                coarse_aggregate02_grading = CementDatabase.getGrading(coarse_aggregate02_grading_name);
                this.previousCoarse02Grading = coarse_aggregate02_grading_name;
                return false;
            }
        } else if (!this.checkCoarseAggregate02Grading(coarse02GradingString)) {
            this.setCoarse_aggregate02_grading_name(this.previousCoarse02Grading);
            coarse_aggregate02_grading = CementDatabase.getGrading(coarse_aggregate02_grading_name);
            this.previousCoarse02Grading = coarse_aggregate02_grading_name;
            return false;
        }

        coarse_aggregate02_grading = coarse02GradingString;
        String[][] grading = getGradingFromString(coarse_aggregate02_grading);
        this.setCoarse_aggregate02_grading_massfrac_0(grading[2][0]);
        this.setCoarse_aggregate02_grading_massfrac_1(grading[2][1]);
        this.setCoarse_aggregate02_grading_massfrac_2(grading[2][2]);
        this.setCoarse_aggregate02_grading_massfrac_3(grading[2][3]);
        this.setCoarse_aggregate02_grading_massfrac_4(grading[2][4]);
        this.setCoarse_aggregate02_grading_massfrac_5(grading[2][5]);
        this.setCoarse_aggregate02_grading_massfrac_6(grading[2][6]);
        this.setCoarse_aggregate02_grading_massfrac_7(grading[2][7]);
        this.setCoarse_aggregate02_grading_massfrac_8(grading[2][8]);
        this.setCoarse_aggregate02_grading_massfrac_9(grading[2][9]);
        this.setCoarse_aggregate02_grading_massfrac_10(grading[2][10]);
        this.setCoarse_aggregate02_grading_massfrac_11(grading[2][11]);
        this.setCoarse_aggregate02_grading_massfrac_12(grading[2][12]);
        this.setCoarse_aggregate02_grading_massfrac_13(grading[2][13]);
        this.setCoarse_aggregate02_grading_massfrac_14(grading[2][14]);
        this.setCoarse_aggregate02_grading_massfrac_15(grading[2][15]);
        this.setCoarse_aggregate02_grading_massfrac_16(grading[2][16]);
        this.setCoarse_aggregate02_grading_massfrac_17(grading[2][17]);
        this.setCoarse_aggregate02_grading_massfrac_18(grading[2][18]);
        this.setCoarse_aggregate02_grading_massfrac_19(grading[2][19]);
        this.setCoarse_aggregate02_grading_massfrac_20(grading[2][20]);
        this.setCoarse_aggregate02_grading_massfrac_21(grading[2][21]);
        this.setCoarse_aggregate02_grading_massfrac_22(grading[2][22]);

        double sum = 0.0;
        for (int i = 0; i < grading[2].length; i++) {
            if (Double.parseDouble(grading[2][i]) > 0.0) {
                sum += Double.parseDouble(grading[2][i]);
            }
        }

        this.setCoarse_aggregate02_grading_total_massfrac(String.valueOf(sum));
        coarse_aggregate02_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(coarse_aggregate02_grading_name));
        this.setCoarse_aggregate02_grading_max_diam(coarse_aggregate02_grading_max_diam);
        return true;
    }

    public boolean updateFineAggregate02Grading() throws SQLArgumentException, SQLException, ParseException {
        String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
        String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
        String coarse01GradingString,coarse02GradingString;
        if (isAdd_coarse_aggregate01()) {
            coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
            coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
            if (!this.checkAllAggregateGradingsAtOnce(coarse01GradingString, coarse02GradingString, fine01GradingString, fine02GradingString)) {
                this.setFine_aggregate02_grading_name(this.previousFine02Grading);
                fine_aggregate02_grading = CementDatabase.getGrading(fine_aggregate02_grading_name);
                this.previousFine02Grading = fine_aggregate02_grading_name;
                return false;
            }
        } else if (!this.checkFineAggregate02Grading(fine02GradingString)) {
            this.setFine_aggregate02_grading_name(this.previousFine02Grading);
            fine_aggregate02_grading = CementDatabase.getGrading(fine_aggregate02_grading_name);
            this.previousFine02Grading = fine_aggregate02_grading_name;
            return false;
        }

        fine_aggregate02_grading = fine02GradingString;
        String[][] grading = getGradingFromString(fine_aggregate02_grading);
        this.setFine_aggregate02_grading_massfrac_0(grading[2][0]);
        this.setFine_aggregate02_grading_massfrac_1(grading[2][1]);
        this.setFine_aggregate02_grading_massfrac_2(grading[2][2]);
        this.setFine_aggregate02_grading_massfrac_3(grading[2][3]);
        this.setFine_aggregate02_grading_massfrac_4(grading[2][4]);
        this.setFine_aggregate02_grading_massfrac_5(grading[2][5]);
        this.setFine_aggregate02_grading_massfrac_6(grading[2][6]);
        this.setFine_aggregate02_grading_massfrac_7(grading[2][7]);
        this.setFine_aggregate02_grading_massfrac_8(grading[2][8]);
        this.setFine_aggregate02_grading_massfrac_9(grading[2][9]);
        this.setFine_aggregate02_grading_massfrac_10(grading[2][10]);
        this.setFine_aggregate02_grading_massfrac_11(grading[2][11]);
        this.setFine_aggregate02_grading_massfrac_12(grading[2][12]);
        this.setFine_aggregate02_grading_massfrac_13(grading[2][13]);
        this.setFine_aggregate02_grading_massfrac_14(grading[2][14]);
        this.setFine_aggregate02_grading_massfrac_15(grading[2][15]);
        this.setFine_aggregate02_grading_massfrac_16(grading[2][16]);
        this.setFine_aggregate02_grading_massfrac_17(grading[2][17]);
        this.setFine_aggregate02_grading_massfrac_18(grading[2][18]);
        this.setFine_aggregate02_grading_massfrac_19(grading[2][19]);
        this.setFine_aggregate02_grading_massfrac_20(grading[2][20]);
        this.setFine_aggregate02_grading_massfrac_21(grading[2][21]);
        this.setFine_aggregate02_grading_massfrac_22(grading[2][22]);
        this.setFine_aggregate02_grading_massfrac_23(grading[2][23]);
        this.setFine_aggregate02_grading_massfrac_24(grading[2][24]);
        this.setFine_aggregate02_grading_massfrac_25(grading[2][25]);
        this.setFine_aggregate02_grading_massfrac_26(grading[2][26]);
        this.setFine_aggregate02_grading_massfrac_27(grading[2][27]);
        this.setFine_aggregate02_grading_massfrac_28(grading[2][28]);
        this.setFine_aggregate02_grading_massfrac_29(grading[2][29]);
        this.setFine_aggregate02_grading_massfrac_30(grading[2][30]);

        fine_aggregate02_grading_max_diam = String.valueOf(CementDatabase.getGradingMaxDiameter(fine_aggregate02_grading_name));
        this.setFine_aggregate02_grading_max_diam(fine_aggregate02_grading_max_diam);
        return true;
    }

    public boolean checkCoarseAggregate02Grading() throws SQLArgumentException, SQLException, ParseException {
        String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
        String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);
        if (isAdd_fine_aggregate01()) {
            String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
            String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);
            return checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString,fine01GradingString,fine02GradingString);
        } else {
            return checkCoarseAggregate02Grading(coarse02GradingString);
        }
    }

    public boolean checkCoarseAggregate02Grading(String coarse02GradingString) throws ParseException {
        // check if the biggest present sieve isn't too big for the system size and if the smallest one is not too small
        String[][] coarse02Grading = getGradingFromString(coarse02GradingString);
        double biggestPresentSieveDiameter = 0.0;
        double smallestPresentSieveDiameter = 0.0;
        boolean biggestPresentSieveFound = false;
        double cG2i = 0.0;
        for (int i = 0; i < coarse02Grading[2].length; i++) {
            cG2i = Double.parseDouble(coarse02Grading[2][i]);

            if (cG2i > 0.0) {
                if (biggestPresentSieveFound == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter = Double.parseDouble(this.getFine_aggregate02_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter = Double.parseDouble(coarse02Grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound = true;
                smallestPresentSieveDiameter = Double.parseDouble(coarse02Grading[1][i]);
            }
        }
        double res = Double.parseDouble(this.getConcrete_resolution());

        double newRes = smallestPresentSieveDiameter/Constants.RESOLUTION_SAFETY_COEFFICIENT;
        newRes *= 100.00;
        double roundedNewRes = Math.round(newRes);
        roundedNewRes /= 100.00;

        double xDim = 0.0;
        double minDim = 0.0;
        xDim = Double.parseDouble(this.getConcrete_x_dim());

        minDim = xDim;
        double yDim = Double.parseDouble(this.getConcrete_y_dim());
        if (yDim < minDim) {
            minDim = yDim;
        }
        double zDim = Double.parseDouble(this.getConcrete_z_dim());
        if (zDim < minDim) {
                minDim = zDim;
        }

        // double maxSize = Constants.SIZE_SAFETY_COEFFICIENT * minDim;
        // if (biggestPresentSieveDiameter > maxSize) {
            minDim = (double)(biggestPresentSieveDiameter/(Constants.SIZE_SAFETY_COEFFICIENT));
            int resMultiples = (int) (minDim/roundedNewRes + 0.5);
            minDim = roundedNewRes * resMultiples;

            minDim *= 100.00;
            double roundedMinDim =  Math.round(minDim);
            roundedMinDim /= 100.0;
            // DecimalFormat TwoDP = new DecimalFormat("#0.00");
            // String formattedMinDim = TwoDP.format(roundedMinDim);
            // String formattedNewRes = TwoDP.format(roundedNewRes);
            this.setConcrete_x_dim(Double.toString(roundedMinDim));
            this.setConcrete_y_dim(Double.toString(roundedMinDim));
            this.setConcrete_z_dim(Double.toString(roundedMinDim));
        // }

        // double minSize = Constants.RESOLUTION_SAFETY_COEFFICIENT * Double.parseDouble(this.getConcrete_resolution());
        // if (smallestPresentSieveDiameter < minSize) {
            this.setConcrete_resolution(Double.toString(roundedNewRes));
        // }

        return true;
    }

    public boolean checkAllAggregateGradingsAtOnce(String coarse01GradingString, String coarse02GradingString, String fine01GradingString, String fine02GradingString) throws ParseException {
        // check if the biggest present sieve isn't too big for the system size and if the smallest one is not too small
        String[][] coarse01Grading = getGradingFromString(coarse01GradingString);
        String[][] fine01Grading = getGradingFromString(fine01GradingString);
        String[][] coarse02Grading = getGradingFromString(coarse02GradingString);
        String[][] fine02Grading = getGradingFromString(fine02GradingString);
        double biggestPresentSieveDiameter = 0.0;
        double smallestPresentSieveDiameter = 0.0;
        double biggestPresentSieveDiameter01 = 0.0;
        double smallestPresentSieveDiameter01 = 0.0;
        double biggestPresentSieveDiameter02 = 0.0;
        double smallestPresentSieveDiameter02 = 0.0;

        boolean biggestPresentSieveFound01 = false;
        boolean smallestPresentSieveFound01 = false;
        boolean biggestPresentSieveFound02 = false;
        boolean smallestPresentSieveFound02 = false;
        boolean biggestPresentSieveFound = false;
        boolean smallestPresentSieveFound = false;
        double cG2i,fG2i;
        cG2i = fG2i = 0.0;
        for (int i = 0; i < coarse01Grading[2].length; i++) {
            cG2i = Double.parseDouble(coarse01Grading[2][i]);
            if (cG2i > 0.0) {
                if (biggestPresentSieveFound01 == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter01 = Double.parseDouble(this.getCoarse_aggregate01_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter01 = Double.parseDouble(coarse01Grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound01 = true;
            }
        }
        for (int i = 0; i < coarse01Grading[2].length; i++) {
            cG2i = Double.parseDouble(coarse01Grading[2][i]);
            if (cG2i > 0.0) {
                if (biggestPresentSieveFound02 == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter02 = Double.parseDouble(this.getCoarse_aggregate02_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter02 = Double.parseDouble(coarse02Grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound02 = true;
            }
        }

        if (biggestPresentSieveFound01 || biggestPresentSieveFound02) {
            biggestPresentSieveFound = true;
            biggestPresentSieveDiameter = biggestPresentSieveDiameter01;
            if (biggestPresentSieveDiameter02 > biggestPresentSieveDiameter) {
                biggestPresentSieveDiameter = biggestPresentSieveDiameter02;
            }
        }

        for (int i = fine01Grading[2].length - 1; i >= 0; i--) {
            fG2i = Double.parseDouble(fine01Grading[2][i]);
            if (fG2i > 0.0) {
                if (smallestPresentSieveFound01 == false) {
                    if (i == 0) {
                        smallestPresentSieveDiameter01 = Double.parseDouble(this.getFine_aggregate01_grading_max_diam());
                    } else {
                        smallestPresentSieveDiameter01 = Double.parseDouble(fine01Grading[1][i - 1]);
                    }
                }
                smallestPresentSieveFound01 = true;
            }
        }

        for (int i = fine02Grading[2].length - 1; i >= 0; i--) {
            fG2i = Double.parseDouble(fine02Grading[2][i]);
            if (fG2i > 0.0) {
                if (smallestPresentSieveFound02 == false) {
                    if (i == 0) {
                        smallestPresentSieveDiameter02 = Double.parseDouble(this.getFine_aggregate02_grading_max_diam());
                    } else {
                        smallestPresentSieveDiameter02 = Double.parseDouble(fine02Grading[1][i - 1]);
                    }
                }
                smallestPresentSieveFound02 = true;
            }
        }

        if (smallestPresentSieveFound01 || smallestPresentSieveFound02) {
            smallestPresentSieveFound = true;
            smallestPresentSieveDiameter = smallestPresentSieveDiameter01;
            if (smallestPresentSieveDiameter02 < smallestPresentSieveDiameter) {
                smallestPresentSieveDiameter = smallestPresentSieveDiameter02;
            }
        }

        double res = Double.parseDouble(this.getConcrete_resolution());
        double newRes = smallestPresentSieveDiameter/Constants.RESOLUTION_SAFETY_COEFFICIENT;
        newRes *= 100.00;
        double roundedNewRes = Math.round(newRes);
        roundedNewRes /= 100.00;


        // double maxSize = Constants.SIZE_SAFETY_COEFFICIENT * minDim;
        double minDim = (double)(biggestPresentSieveDiameter/(Constants.SIZE_SAFETY_COEFFICIENT));
        int resMultiples = (int) (minDim/roundedNewRes + 0.5);
        minDim = roundedNewRes * resMultiples;

        minDim *= 100.00;
        double roundedMinDim =  Math.round(minDim);
        roundedMinDim /= 100.0;
        // DecimalFormat TwoDP = new DecimalFormat("#0.00");
        // String formattedMinDim = TwoDP.format(roundedMinDim);
        // String formattedNewRes = TwoDP.format(roundedNewRes);
        this.setConcrete_x_dim(Double.toString(roundedMinDim));
        this.setConcrete_y_dim(Double.toString(roundedMinDim));
        this.setConcrete_z_dim(Double.toString(roundedMinDim));

        // double minSize = Constants.RESOLUTION_SAFETY_COEFFICIENT * Double.parseDouble(this.getConcrete_resolution());
        // if (smallestPresentSieveDiameter < minSize) {
            this.setConcrete_resolution(Double.toString(roundedNewRes));
        // }

        return true;
    }

    public boolean checkFineAggregate01Grading() throws SQLArgumentException, SQLException, ParseException {
        String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
        String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);

        if (isAdd_coarse_aggregate01()) {
            String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
            String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);

            return checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString, fine01GradingString, fine02GradingString);
        } else {
            return checkFineAggregate01Grading(fine01GradingString);
        }
    }
    
    public boolean checkFineAggregate01Grading(String gradingString) throws ParseException {
        // check if the biggest present sieve isn't too big for the system size and if the smallest one is not too small
        String[][] grading = getGradingFromString(gradingString);
        double biggestPresentSieveDiameter = 0.0;
        double smallestPresentSieveDiameter = 0.0;
        boolean biggestPresentSieveFound = false;
        double g2i = 0.0;
        // Find smallest sieve first, and set resolution
        // Find largest sieve next, and set size
        // Round size to nearest value consistent with being an integer
        //    multiple of the resolution.

        for (int i = 0; i < grading[2].length; i++) {
            g2i = Double.parseDouble(grading[2][i]);
            if (g2i > 0.0) {
                if (biggestPresentSieveFound == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter = Double.parseDouble(this.getFine_aggregate01_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter = Double.parseDouble(grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound = true;
                smallestPresentSieveDiameter = Double.parseDouble(grading[1][i]);
            }
        }
        double res = Double.parseDouble(this.getConcrete_resolution());
        
        double newRes = smallestPresentSieveDiameter/Constants.RESOLUTION_SAFETY_COEFFICIENT;
        newRes *= 100.00;
        double roundedNewRes = Math.round(newRes);
        roundedNewRes /= 100.00;

        double minDim = (double)(biggestPresentSieveDiameter/(Constants.SIZE_SAFETY_COEFFICIENT));
        int resMultiples = (int) (minDim/roundedNewRes + 0.5);
        minDim = roundedNewRes * resMultiples;

        minDim *= 100.00;
        double roundedMinDim =  Math.round(minDim);
        roundedMinDim /= 100.0;
        // DecimalFormat TwoDP = new DecimalFormat("#0.00");
        // String formattedMinDim = TwoDP.format(roundedMinDim);
        // String formattedNewRes = TwoDP.format(roundedNewRes);
        this.setConcrete_x_dim(Double.toString(roundedMinDim));
        this.setConcrete_y_dim(Double.toString(roundedMinDim));
        this.setConcrete_z_dim(Double.toString(roundedMinDim));
        
        this.setConcrete_resolution(Double.toString(roundedNewRes));
        
        return true;
    }
    public boolean checkFineAggregate02Grading() throws SQLArgumentException, SQLException, ParseException {
        String fine01GradingString = CementDatabase.getGrading(fine_aggregate01_grading_name);
        String fine02GradingString = CementDatabase.getGrading(fine_aggregate02_grading_name);

        if (isAdd_coarse_aggregate01()) {
            String coarse01GradingString = CementDatabase.getGrading(coarse_aggregate01_grading_name);
            String coarse02GradingString = CementDatabase.getGrading(coarse_aggregate02_grading_name);

            return checkAllAggregateGradingsAtOnce(coarse01GradingString,coarse02GradingString, fine01GradingString, fine02GradingString);
        } else {
            return checkFineAggregate02Grading(fine01GradingString);
        }
    }

    public boolean checkFineAggregate02Grading(String gradingString) throws ParseException {
        // check if the biggest present sieve isn't too big for the system size and if the smallest one is not too small
        String[][] grading = getGradingFromString(gradingString);
        double biggestPresentSieveDiameter = 0.0;
        double smallestPresentSieveDiameter = 0.0;
        boolean biggestPresentSieveFound = false;
        double g2i = 0.0;
        // Find smallest sieve first, and set resolution
        // Find largest sieve next, and set size
        // Round size to nearest value consistent with being an integer
        //    multiple of the resolution.

        for (int i = 0; i < grading[2].length; i++) {
            g2i = Double.parseDouble(grading[2][i]);
            if (g2i > 0.0) {
                if (biggestPresentSieveFound == false) {
                    if (i == 0) {
                        biggestPresentSieveDiameter = Double.parseDouble(this.getFine_aggregate01_grading_max_diam());
                    } else {
                        biggestPresentSieveDiameter = Double.parseDouble(grading[1][i - 1]);
                    }
                }
                biggestPresentSieveFound = true;
                smallestPresentSieveDiameter = Double.parseDouble(grading[1][i]);
            }
        }
        double res = Double.parseDouble(this.getConcrete_resolution());

        double newRes = smallestPresentSieveDiameter/Constants.RESOLUTION_SAFETY_COEFFICIENT;
        newRes *= 100.00;
        double roundedNewRes = Math.round(newRes);
        roundedNewRes /= 100.00;

        double minDim = (double)(biggestPresentSieveDiameter/(Constants.SIZE_SAFETY_COEFFICIENT));
        int resMultiples = (int) (minDim/roundedNewRes + 0.5);
        minDim = roundedNewRes * resMultiples;

        minDim *= 100.00;
        double roundedMinDim =  Math.round(minDim);
        roundedMinDim /= 100.0;
        // DecimalFormat TwoDP = new DecimalFormat("#0.00");
        // String formattedMinDim = TwoDP.format(roundedMinDim);
        // String formattedNewRes = TwoDP.format(roundedNewRes);
        this.setConcrete_x_dim(Double.toString(roundedMinDim));
        this.setConcrete_y_dim(Double.toString(roundedMinDim));
        this.setConcrete_z_dim(Double.toString(roundedMinDim));

        this.setConcrete_resolution(Double.toString(roundedNewRes));

        return true;
    }

    public void updateCoarseAggregate01SpecificGravity() throws SQLArgumentException, SQLException, ParseException {
        coarse_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate01_display_name));
        updateMixVolumeFractions();
    }
    
    public void updateFineAggregate01Name() throws SQLArgumentException, SQLException {
        fine_aggregate01_name = CementDatabase.getAggregateNameWithDisplayName(fine_aggregate01_display_name);
    }

    public void updateCoarseAggregate01Name() throws SQLArgumentException, SQLException {
        coarse_aggregate01_name = CementDatabase.getAggregateNameWithDisplayName(coarse_aggregate01_display_name);
    }

    public void updateFineAggregate01() throws SQLArgumentException, SQLException, ParseException {
        fine_aggregate01_name = CementDatabase.getAggregateNameWithDisplayName(fine_aggregate01_display_name);
        fine_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate01_display_name));
        updateMixVolumeFractions();
    }

    public void updateCoarseAggregate01() throws SQLArgumentException, SQLException, ParseException {
        coarse_aggregate01_name = CementDatabase.getAggregateNameWithDisplayName(coarse_aggregate01_display_name);
        coarse_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate01_display_name));
        updateMixVolumeFractions();
    }

    public void updateFineAggregate01SpecificGravity() throws SQLArgumentException, SQLException, ParseException {
        fine_aggregate01_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate01_display_name));
        updateMixVolumeFractions();
    }

    public void updateCoarseAggregate02SpecificGravity() throws SQLArgumentException, SQLException, ParseException {
        coarse_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate02_display_name));
        updateMixVolumeFractions();
    }

    public void updateFineAggregate02Name() throws SQLArgumentException, SQLException {
        fine_aggregate02_name = CementDatabase.getAggregateNameWithDisplayName(fine_aggregate02_display_name);
    }

    public void updateCoarseAggregate02Name() throws SQLArgumentException, SQLException {
        coarse_aggregate02_name = CementDatabase.getAggregateNameWithDisplayName(coarse_aggregate02_display_name);
    }

    public void updateFineAggregate02() throws SQLArgumentException, SQLException, ParseException {
        fine_aggregate02_name = CementDatabase.getAggregateNameWithDisplayName(fine_aggregate02_display_name);
        fine_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate02_display_name));
        updateMixVolumeFractions();
    }

    public void updateCoarseAggregate02() throws SQLArgumentException, SQLException, ParseException {
        coarse_aggregate02_name = CementDatabase.getAggregateNameWithDisplayName(coarse_aggregate02_display_name);
        coarse_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(coarse_aggregate02_display_name));
        updateMixVolumeFractions();
    }

    public void updateFineAggregate02SpecificGravity() throws SQLArgumentException, SQLException, ParseException {
        fine_aggregate02_sg = String.valueOf(CementDatabase.getAggregateSpecificGravity(fine_aggregate02_display_name));
        updateMixVolumeFractions();
    }

    /**
     * Holds value of property binder_sg.
     */
    private String binder_sg;
    
    /**
     * Getter for property binder_sg.
     * @return Value of property binder_sg.
     */
    public String getBinder_sg() {
        return this.binder_sg;
    }
    
    /**
     * Setter for property binder_sg.
     * @param binder_sg New value of property binder_sg.
     */
    public void setBinder_sg(String binder_sg) {
        this.binder_sg = binder_sg;
    }
    
    /**
     * Holds value of property coarse_aggregate01_volfrac.
     */
    private String coarse_aggregate01_volfrac;
    
    /**
     * Getter for property coarse_aggregate01_volfrac.
     * @return Value of property coarse_aggregate01_volfrac.
     */
    public String getCoarse_aggregate01_volfrac() {
        return this.coarse_aggregate01_volfrac;
    }
    
    /**
     * Setter for property coarse_aggregate01_volfrac.
     * @param coarse_aggregate01_volfrac New value of property coarse_aggregate01_volfrac.
     */
    public void setCoarse_aggregate01_volfrac(String coarse_aggregate01_volfrac) {
        this.coarse_aggregate01_volfrac = coarse_aggregate01_volfrac;
    }
    
    /**
     * Holds value of property fine_aggregate01_volfrac.
     */
    private String fine_aggregate01_volfrac;
    
    /**
     * Getter for property fine_aggregate01_volfrac.
     * @return Value of property fine_aggregate01_volfrac.
     */
    public String getFine_aggregate01_volfrac() {
        return this.fine_aggregate01_volfrac;
    }
    
    /**
     * Setter for property fine_aggregate01_volfrac.
     * @param fine_aggregate01_volfrac New value of property fine_aggregate01_volfrac.
     */
    public void setFine_aggregate01_volfrac(String fine_aggregate01_volfrac) {
        this.fine_aggregate01_volfrac = fine_aggregate01_volfrac;
    }

    /**
     * Holds value of property coarse_aggregate02_volfrac.
     */
    private String coarse_aggregate02_volfrac;

    /**
     * Getter for property coarse_aggregate02_volfrac.
     * @return Value of property coarse_aggregate02_volfrac.
     */
    public String getCoarse_aggregate02_volfrac() {
        return this.coarse_aggregate02_volfrac;
    }

    /**
     * Setter for property coarse_aggregate02_volfrac.
     * @param coarse_aggregate02_volfrac New value of property coarse_aggregate02_volfrac.
     */
    public void setCoarse_aggregate02_volfrac(String coarse_aggregate02_volfrac) {
        this.coarse_aggregate02_volfrac = coarse_aggregate02_volfrac;
    }

    /**
     * Holds value of property fine_aggregate02_volfrac.
     */
    private String fine_aggregate02_volfrac;

    /**
     * Getter for property fine_aggregate02_volfrac.
     * @return Value of property fine_aggregate02_volfrac.
     */
    public String getFine_aggregate02_volfrac() {
        return this.fine_aggregate02_volfrac;
    }

    /**
     * Setter for property fine_aggregate02_volfrac.
     * @param fine_aggregate02_volfrac New value of property fine_aggregate02_volfrac.
     */
    public void setFine_aggregate02_volfrac(String fine_aggregate02_volfrac) {
        this.fine_aggregate02_volfrac = fine_aggregate02_volfrac;
    }

    /**
     * Holds value of property water_binder_ratio.
     */
    private String water_binder_ratio;
    
    /**
     * Getter for property water_binder_ratio.
     * @return Value of property water_binder_ratio.
     */
    public String getWater_binder_ratio() {
        return this.water_binder_ratio;
    }
    
    /**
     * Setter for property water_binder_ratio.
     * @param water_binder_ratio New value of property water_binder_ratio.
     */
    public void setWater_binder_ratio(String water_binder_ratio) {
        this.water_binder_ratio = water_binder_ratio;
    }
    
    public void updateMixVolumeFractions() throws ParseException {
        /* Update binder, coarse aggregate, fine aggregate and water volume fraction*/
        double sumMass = 0.0;
        double sumVolume = 0.0;
        
        updateBinderSpecificGravity();
        double binderSpecificGravity = Double.parseDouble(binder_sg);
        
        /* Binder */
        double binderMassFraction = Double.parseDouble(binder_massfrac);
        sumMass = sumMass + binderMassFraction;
        double binderVolume = binderMassFraction/binderSpecificGravity;
        sumVolume = sumVolume + binderVolume;
        
        /* Coarse aggregate 01*/
        double mfi = Double.parseDouble(coarse_aggregate01_massfrac);
        sumMass = sumMass + mfi;
        double coarseAggregateSpecificGravity = Double.parseDouble(coarse_aggregate01_sg);
        double coarseAggregate01Volume = mfi/coarseAggregateSpecificGravity;
        sumVolume = sumVolume + coarseAggregate01Volume;

        /* Coarse aggregate 02*/
        mfi = Double.parseDouble(coarse_aggregate02_massfrac);
        sumMass = sumMass + mfi;
        coarseAggregateSpecificGravity = Double.parseDouble(coarse_aggregate02_sg);
        double coarseAggregate02Volume = mfi/coarseAggregateSpecificGravity;
        sumVolume = sumVolume + coarseAggregate02Volume;

        /* Fine aggregate 01 */
        mfi = Double.parseDouble(fine_aggregate01_massfrac);
        sumMass = sumMass + mfi;
        double fineAggregateSpecificGravity = Double.parseDouble(fine_aggregate01_sg);
        double fineAggregate01Volume = mfi/fineAggregateSpecificGravity;
        sumVolume = sumVolume + fineAggregate01Volume;

        /* Fine aggregate 02 */
        mfi = Double.parseDouble(fine_aggregate02_massfrac);
        sumMass = sumMass + mfi;
        fineAggregateSpecificGravity = Double.parseDouble(fine_aggregate02_sg);
        double fineAggregate02Volume = mfi/fineAggregateSpecificGravity;
        sumVolume = sumVolume + fineAggregate02Volume;

        /* Water */
        mfi = Double.parseDouble(water_massfrac);
        sumMass = sumMass + mfi;
        double waterVolume = mfi/Constants.WATER_DENSITY;
        sumVolume = sumVolume + waterVolume;
        
        // Set water/solid ratio
        water_binder_ratio = Double.toString(Util.round(mfi/binderMassFraction,3));
        
        double volumeFraction = binderVolume/sumVolume;
        binder_volfrac = Double.toString(Util.round(volumeFraction,4));
        volumeFraction = coarseAggregate01Volume/sumVolume;
        coarse_aggregate01_volfrac = Double.toString(Util.round(volumeFraction,4));
        volumeFraction = fineAggregate01Volume/sumVolume;
        fine_aggregate01_volfrac = Double.toString(Util.round(volumeFraction,4));
        volumeFraction = coarseAggregate02Volume/sumVolume;
        coarse_aggregate02_volfrac = Double.toString(Util.round(volumeFraction,4));
        volumeFraction = fineAggregate02Volume/sumVolume;
        fine_aggregate02_volfrac = Double.toString(Util.round(volumeFraction,4));

        volumeFraction = waterVolume/sumVolume;
        water_volfrac = Double.toString(Util.round(volumeFraction,4));
    }
    
    /**
     * Holds value of property add_coarse_aggregate01.
     */
    private boolean add_coarse_aggregate01;
    
    /**
     * Getter for property add_coarse_aggregate01.
     * @return Value of property add_coarse_aggregate01.
     */
    public boolean isAdd_coarse_aggregate01() {
        return this.add_coarse_aggregate01;
    }
    
    /**
     * Setter for property add_coarse_aggregate01.
     * @param add_coarse_aggregate01 New value of property add_coarse_aggregate01.
     */
    public void setAdd_coarse_aggregate01(boolean add_coarse_aggregate01) {
        this.add_coarse_aggregate01 = add_coarse_aggregate01;
    }
    
    /**
     * Holds value of property add_fine_aggregate01.
     */
    private boolean add_fine_aggregate01;
    
    /**
     * Getter for property add_fine_aggregate01.
     * @return Value of property add_fine_aggregate01.
     */
    public boolean isAdd_fine_aggregate01() {
        return this.add_fine_aggregate01;
    }
    
    /**
     * Setter for property add_fine_aggregate01.
     * @param add_fine_aggregate01 New value of property add_fine_aggregate01.
     */
    public void setAdd_fine_aggregate01(boolean add_fine_aggregate01) {
        this.add_fine_aggregate01 = add_fine_aggregate01;
    }

    /**
     * Holds value of property add_coarse_aggregate02.
     */
    private boolean add_coarse_aggregate02;

    /**
     * Getter for property add_coarse_aggregate02.
     * @return Value of property add_coarse_aggregate02.
     */
    public boolean isAdd_coarse_aggregate02() {
        return this.add_coarse_aggregate02;
    }

    /**
     * Setter for property add_coarse_aggregate02.
     * @param add_coarse_aggregate02 New value of property add_coarse_aggregate02.
     */
    public void setAdd_coarse_aggregate02(boolean add_coarse_aggregate02) {
        this.add_coarse_aggregate02 = add_coarse_aggregate02;
    }

    /**
     * Holds value of property add_fine_aggregate02.
     */
    private boolean add_fine_aggregate02;

    /**
     * Getter for property add_fine_aggregate02.
     * @return Value of property add_fine_aggregate02.
     */
    public boolean isAdd_fine_aggregate02() {
        return this.add_fine_aggregate02;
    }

    /**
     * Setter for property add_fine_aggregate02.
     * @param add_fine_aggregate02 New value of property add_fine_aggregate02.
     */
    public void setAdd_fine_aggregate02(boolean add_fine_aggregate02) {
        this.add_fine_aggregate02 = add_fine_aggregate02;
    }
    
    /**
     * Holds value of property air_volfrac.
     */
    private String air_volfrac;
    
    /**
     * Getter for property air_volfrac.
     * @return Value of property air_volfrac.
     */
    public String getAir_volfrac() {
        return this.air_volfrac;
    }
    
    /**
     * Setter for property air_volfrac.
     * @param air_volfrac New value of property air_volfrac.
     */
    public void setAir_volfrac(String air_volfrac) {
        this.air_volfrac = air_volfrac;
    }
    
    /**
     * Holds value of property add_fly_ash.
     */
    private boolean add_fly_ash;
    
    /**
     * Getter for property add_fly_ash.
     * @return Value of property add_fly_ash.
     */
    public boolean isAdd_fly_ash() {
        return this.add_fly_ash;
    }
    
    /**
     * Setter for property add_fly_ash.
     * @param add_fly_ash New value of property add_fly_ash.
     */
    public void setAdd_fly_ash(boolean add_fly_ash) {
        this.add_fly_ash = add_fly_ash;
    }
    
    /**
     * Holds value of property add_slag.
     */
    private boolean add_slag;
    
    /**
     * Getter for property add_slag.
     * @return Value of property add_slag.
     */
    public boolean isAdd_slag() {
        return this.add_slag;
    }
    
    /**
     * Setter for property add_slag.
     * @param add_slag New value of property add_slag.
     */
    public void setAdd_slag(boolean add_slag) {
        this.add_slag = add_slag;
    }
    
    /**
     * Holds value of property add_inert_filler.
     */
    private boolean add_inert_filler;
    
    /**
     * Getter for property add_inert_filler.
     * @return Value of property add_inert_filler.
     */
    public boolean isAdd_inert_filler() {
        return this.add_inert_filler;
    }
    
    /**
     * Setter for property add_inert_filler.
     * @param add_inert_filler New value of property add_inert_filler.
     */
    public void setAdd_inert_filler(boolean add_inert_filler) {
        this.add_inert_filler = add_inert_filler;
    }
    
    /**
     * Holds value of property add_silica_fume.
     */
    private boolean add_silica_fume;
    
    /**
     * Getter for property add_silica_fume.
     * @return Value of property add_silica_fume.
     */
    public boolean isAdd_silica_fume() {
        return this.add_silica_fume;
    }
    
    /**
     * Setter for property add_silica_fume.
     * @param add_silica_fume New value of property add_silica_fume.
     */
    public void setAdd_silica_fume(boolean add_silica_fume) {
        this.add_silica_fume = add_silica_fume;
    }
    
    /**
     * Holds value of property add_caco3.
     */
    private boolean add_caco3;
    
    /**
     * Getter for property add_caco3.
     * @return Value of property add_caco3.
     */
    public boolean isAdd_caco3() {
        return this.add_caco3;
    }
    
    /**
     * Setter for property add_caco3.
     * @param add_caco3 New value of property add_caco3.
     */
    public void setAdd_caco3(boolean add_caco3) {
        this.add_caco3 = add_caco3;
    }
    
    /**
     * Holds value of property add_free_lime.
     */
    private boolean add_free_lime;
    
    /**
     * Getter for property add_free_lime.
     * @return Value of property add_free_lime.
     */
    public boolean isAdd_free_lime() {
        return this.add_free_lime;
    }
    
    /**
     * Setter for property add_free_lime.
     * @param add_free_lime New value of property add_free_lime.
     */
    public void setAdd_free_lime(boolean add_free_lime) {
        this.add_free_lime = add_free_lime;
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
     * Holds value of property use_flocculation.
     */
    private boolean use_flocculation;
    
    /**
     * Getter for property use_flocculation.
     * @return Value of property use_flocculation.
     */
    public boolean isUse_flocculation() {
        return this.use_flocculation;
    }
    
    /**
     * Setter for property use_flocculation.
     * @param use_flocculation New value of property use_flocculation.
     */
    public void setUse_flocculation(boolean use_flocculation) {
        this.use_flocculation = use_flocculation;
    }
    
    /**
     * Holds value of property use_dispersion_distance.
     */
    private boolean use_dispersion_distance;
    
    /**
     * Getter for property use_dispersion_distance.
     * @return Value of property use_dispersion_distance.
     */
    public boolean isUse_dispersion_distance() {
        return this.use_dispersion_distance;
    }
    
    /**
     * Setter for property use_dispersion_distance.
     * @param use_dispersion_distance New value of property use_dispersion_distance.
     */
    public void setUse_dispersion_distance(boolean use_dispersion_distance) {
        this.use_dispersion_distance = use_dispersion_distance;
    }

     /**
     * Holds value of property use_visualize_concrete_checkbox.
     */
    private boolean use_visualize_concrete;

    /**
     * Getter for property use_visualize_concrete.
     * @return Value of property use_visualize_concrete.
     */
    public boolean isUse_visualize_concrete() {
        return this.use_visualize_concrete;
    }

    /**
     * Setter for property use_visualize_concrete.
     * @param use_visualize_concrete New value of property use_visualize_concrete.
     */
    public void setUse_visualize_concrete(boolean use_visualize_concrete) {
        this.use_visualize_concrete = use_visualize_concrete;
    }
    
    /**
     * Holds value of property concrete_resolution.
     */
    private String concrete_resolution;
    
    /**
     * Getter for property concrete_resolution.
     * @return Value of property concrete_resolution.
     */
    public String getConcrete_resolution() {
        return this.concrete_resolution;
    }
    
    /**
     * Setter for property concrete_resolution.
     * @param concrete_resolution New value of property concrete_resolution.
     */
    public void setConcrete_resolution(String concrete_resolution) {
        this.concrete_resolution = concrete_resolution;
    }
    
    /**
     * Holds value of property concrete_x_dim.
     */
    private String concrete_x_dim;
    
    /**
     * Getter for property concrete_x_dim.
     * @return Value of property concrete_x_dim.
     */
    public String getConcrete_x_dim() {
        return this.concrete_x_dim;
    }
    
    /**
     * Setter for property concrete_x_dim.
     * @param concrete_x_dim New value of property concrete_x_dim.
     */
    public void setConcrete_x_dim(String concrete_x_dim) {
        this.concrete_x_dim = concrete_x_dim;
    }
    
    /**
     * Holds value of property concrete_y_dim.
     */
    private String concrete_y_dim;
    
    /**
     * Getter for property concrete_y_dim.
     * @return Value of property concrete_y_dim.
     */
    public String getConcrete_y_dim() {
        return this.concrete_y_dim;
    }
    
    /**
     * Setter for property concrete_y_dim.
     * @param concrete_y_dim New value of property concrete_y_dim.
     */
    public void setConcrete_y_dim(String concrete_y_dim) {
        this.concrete_y_dim = concrete_y_dim;
    }
    
    /**
     * Holds value of property concrete_z_dim.
     */
    private String concrete_z_dim;
    
    /**
     * Getter for property concrete_z_dim.
     * @return Value of property concrete_z_dim.
     */
    public String getConcrete_z_dim() {
        return this.concrete_z_dim;
    }
    
    /**
     * Setter for property concrete_z_dim.
     * @param concrete_z_dim New value of property concrete_z_dim.
     */
    public void setConcrete_z_dim(String concrete_z_dim) {
        this.concrete_z_dim = concrete_z_dim;
    }
    
    /**
     * Getter for property add_aggregate01.
     * @return Value of property add_aggregate01.
     */
    public boolean isAdd_aggregate01() {
        return (isAdd_coarse_aggregate01() || isAdd_fine_aggregate01());
    }

    /**
     * Getter for property add_aggregate02.
     * @return Value of property add_aggregate02.
     */
    public boolean isAdd_aggregate02() {
        return (isAdd_coarse_aggregate02() || isAdd_fine_aggregate02());
    }

     /**
     * Getter for property add_aggregate.
     * @return Value of property add_aggregate.
     */
    public boolean isAdd_aggregate() {
        return (isAdd_aggregate01() || isAdd_aggregate02());
    }

    private String previousCoarse01Grading;
    
    private String previousFine01Grading;

    private String previousCoarse02Grading;

    private String previousFine02Grading;

    /**
     * Holds value of property fraction_orthorombic_c3a.
     */
    private String fraction_orthorombic_c3a;
    
    /**
     * Getter for property fraction_orthorombic_c3a.
     * @return Value of property fraction_orthorombic_c3a.
     */
    public String getFraction_orthorombic_c3a() {
        return this.fraction_orthorombic_c3a;
    }
    
    /**
     * Setter for property fraction_orthorombic_c3a.
     * @param fraction_orthorombic_c3a New value of property fraction_orthorombic_c3a.
     */
    public void setFraction_orthorombic_c3a(String fraction_orthorombic_c3a) {
        this.fraction_orthorombic_c3a = fraction_orthorombic_c3a;
    }
    
}
