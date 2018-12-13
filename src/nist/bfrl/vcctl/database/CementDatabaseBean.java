/*
 * CementDatabaseBean.java
 *
 * Created on July 18, 2005, 4:23 PM
 */

package nist.bfrl.vcctl.database;

import java.beans.*;
import java.io.Serializable;
import java.sql.SQLException;

import java.util.*;
import nist.bfrl.vcctl.exceptions.*;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.FileTypes;

/**
 * @author tahall
 */
public class CementDatabaseBean extends Object implements Serializable {
    
    
    public CementDatabaseBean() {
        
    }
    
    /**
     * Getter for property psds.
     * @return Value of property psds.
     */
    public List<String> getPsds() throws SQLArgumentException, DBFileException, SQLException {
        return CementDatabase.getPSDFilesNames();
    }
    
    /**
     * Getter for property cements.
     * @return Value of property cements.
     */
    public List<String> getCements() throws NoCementException, SQLException {
        return CementDatabase.getCementNames();
    }
    
    /**
     * Getter for property flyashs.
     * @return Value of property flyashs.
     */
    public List<String> getFlyashs() throws NoFlyAshException, SQLException {
        return CementDatabase.getFlyAshNames();
    }
    
    /**
     * Getter for property slags.
     * @return Value of property slags.
     */
    public List<String> getSlags() throws NoSlagException, SQLException {
        return CementDatabase.getSlagNames();
    }
    
    /**
     * Getter for property inert_fillers.
     * @return Value of property inert_fillers.
     */
    public List<String> getInert_fillers() throws NoInertFillerException, SQLException {
        return CementDatabase.getInertFillerNames();
    }
    
    /**
     * Getter for property alkali_content_of_cements.
     * @return Value of property alkali_content_of_cements.
     */
    /*
    public List<String> getAlkali_content_of_cements() {
        return CementDatabase.getNamesOfType("alkali_cement");
    }
     **/
    
    /**
     * Getter for property alkali_content_of_flyashs.
     * @return Value of property alkali_content_of_flyashs.
     */
    /*
    public List<String> getAlkali_content_of_flyashs() {
        return CementDatabase.getNamesOfType("alkali_flyash");
    }
     **/
    
    /**
     * Getter for property temperature_schedules.
     * @return Value of property temperature_schedules.
     */
    /*
    public List<String> getTemperature_schedules() {
        return CementDatabase.getNamesOfType("temperature_schedule");
    }
     */
    
    /**
     * Getter for property fine_aggregates.
     * @return Value of property fine_aggregates.
     */
    public List<String> getFine_aggregates() throws NoFineAggregateException, SQLArgumentException, SQLException {
        return CementDatabase.getFineAggregateDisplayNames();
    }
    
    /**
     * Getter for property coarse_aggregates.
     * @return Value of property coarse_aggregates.
     */
    public List<String> getCoarse_aggregates() throws NoCoarseAggregateException, SQLArgumentException, SQLException {
        return CementDatabase.getCoarseAggregateDisplayNames();
    }
    
    /**
     * Getter for property fine_aggregate_gradings.
     * @return Value of property fine_aggregate_gradings.
     */
    public List<String> getFine_aggregate_gradings() throws NoFineAggregateGradingException, SQLException, SQLArgumentException {
        return CementDatabase.getFineAggregateGradingNames();
    }
    
    /**
     * Getter for property coarse_aggregate_gradings.
     * @return Value of property coarse_aggregate_gradings.
     */
    public List<String> getCoarse_aggregate_gradings() throws NoCoarseAggregateGradingException, SQLException, SQLArgumentException {
        return CementDatabase.getCoarseAggregateGradingNames();
    }
    
    /**
     * Getter for property particle_shape_sets.
     * @return Value of property particle_shape_sets.
     */
    public List<String> getParticle_shape_sets() throws SQLException, NoParticleShapeSetException {
        List<String> l = new ArrayList();
        l.add(Constants.DEFAULT_PARTICLE_SHAPE_SET); // add "None"
        l.addAll(CementDatabase.getParticleShapeSetNames());
         
        return l;
    }
    
    /**
     * Getter for property alkali_characteristics_files.
     * @return Value of property alkali_characteristics_files.
     */
    /*
    public Collection getAlkali_characteristics_files() {
        List<String> l = CementDatabase.getNamesInTable("alkali_characteristics");
        return l;
    }
     **/
    
    /**
     * Getter for property slag_characteristics_files.
     * @return Value of property slag_characteristics_files.
     */
    /*
    public Collection getSlag_characteristics_files() {
        List<String> l = CementDatabase.getNamesInTable("slag_characteristics");
        return l;
    }
     **/
    
    /**
     * Getter for property alkali_characteristics_files.
     * @return Value of property alkali_characteristics_files.
     */
    public List<String> getAlkali_characteristics_files() throws DBFileException, SQLArgumentException, SQLException {
        return CementDatabase.getAlkaliCharacteristicsFilesNames();
    }
    
    /**
     * Getter for property slag_characteristics_files.
     * @return Value of property slag_characteristics_files.
     */
    public List<String> getSlag_characteristics_files() throws DBFileException, SQLArgumentException, SQLException {
        return CementDatabase.getSlagCharacteristicsFilesNames();
    }
    
    /**
     * Getter for property parameter_files.
     * @return Value of property parameter_files.
     */
    public List<String> getParameter_files() throws DBFileException, SQLArgumentException, SQLException {
        return CementDatabase.getParameterFilesNames();
    }
    
    /**
     * Getter for property chemical_shrinkage_files.
     * @return Value of property chemical_shrinkage_files.
     */
    public List<String> getChemical_shrinkage_files() throws SQLArgumentException, DBFileException, SQLException {
        return CementDatabase.getChemicalShrinkageFilesNames();
    }
    
    /**
     * Getter for property calorimetry_files.
     * @return Value of property calorimetry_files.
     */
    public List<String> getCalorimetry_files() throws SQLArgumentException, DBFileException, SQLException {
        return CementDatabase.getCalorimetryFilesNames();
    }
    
    /**
     * Getter for property timing_output_files.
     * @return Value of property timing_output_files.
     */
    public List<String> getTiming_output_files() throws SQLArgumentException, DBFileException, SQLException {
        return CementDatabase.getTimingOutputFilesNames();
    }
    
    /**
     * Getter for property cement_data_files.
     * @return Value of property cement_data_files.
     */
    public List<String> getCement_data_files() throws SQLArgumentException, DBFileException, SQLException {
        return CementDatabase.getDBFilesNames();
    }
    
    // public List<String> getCement_data_file_types() {
    //     return FileTypes.getTypeDescriptionList();
    // }

    public List<String> getCement_data_file_types() {
       return FileTypes.getTypeDescriptionList();
    }
    
}
