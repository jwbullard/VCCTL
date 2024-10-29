/*
 * ConcreteMeasurementsForm.java
 *
 * Created on July 20, 2007, 10:25 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.measurements;

import java.io.File;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.SortedMap;
import java.util.ArrayList;
import nist.bfrl.vcctl.database.CementDatabase;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.NoHydrationResultsException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.operation.microstructure.GenerateMicrostructureForm;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;
import org.apache.struts.action.ActionForm;

/**
 *
 * @author mscialom
 */
public class ConcreteMeasurementsForm extends ActionForm {

    public void init(String userName) throws NoHydrationResultsException, SQLArgumentException, SQLException {
        if (hydrationName != null) {
            setMicrostructure(OperationDatabase.getDependantOperationForUser(hydrationName, userName));
        }
    }

    /**
     * Creates a new instance of HydratedMixMeasurementsForm
     */
    public ConcreteMeasurementsForm() {
    }
    
    /**
     * Holds value of property hydrationName.
     */
    private String hydrationName;

    /**
     * Getter for property hydrationName.
     * @return Value of property hydrationName.
     */
    public String getHydrationName() {
        return this.hydrationName;
    }

    /**
     * Setter for property hydrationName.
     * @param hydrationName New value of property hydrationName.
     */
    public void setHydrationName(String hydrationName) {
        this.hydrationName = hydrationName;
    }

    /**
     * Holds value of property userFinishedHydratedMixList.
     */
    private Collection<String> userFinishedHydratedMixList;

    /**
     * Getter for property userFinishedHydratedMixList.
     * @return Value of property userFinishedHydratedMixList.
     */
    public Collection<String> getUserFinishedHydratedMixList() {
        return this.userFinishedHydratedMixList;
    }

    /**
     * Setter for property userFinishedHydratedMixList.
     * @param userHydratedMixList New value of property userFinishedHydratedMixList.
     */
    public void setUserFinishedHydratedMixList(Collection<String> userFinishedHydratedMixList) {
        this.userFinishedHydratedMixList = userFinishedHydratedMixList;
    }
    
    /**
     * Holds value of property microstructure.
     */
    private String microstructure;

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

    public String generateElasticInputForUser(String imageFileName, String outputDir, String operationName, String userName) throws SQLArgumentException, SQLException {
        // String filename = this.getMicrostructure().split("/")[1];
        String input = imageFileName + "\n";

        input += "1\n"; // early age connection always set to 1

        String microstruct = this.getMicrostructure();
        UserDirectory userDir = new UserDirectory(userName);

        GenerateMicrostructureForm microstructureForm = GenerateMicrostructureForm.create_from_state(microstruct, userName);

        /* ITZ? */
        if (microstructureForm.isAdd_aggregate()) {
            input += "1\n";
        } else {
            input += "0\n";
        }

        input += outputDir + "\n"; // output directory

        String opName = microstructureForm.getMix_name();
        String pfileName = opName;
        pfileName += ".pimg";

        String pimgpath = userDir.getOperationFilePath(opName, pfileName);
        input += pimgpath + "\n";

        if (microstructureForm.isAdd_aggregate()) {
            // input += ServerFile.getUserOperationDir(userName,Constants.ELASTIC_AGGREGATE_DIRECTORY);

            // operationName = operationName + File.separator + Constants.ELASTIC_AGGREGATE_DIRECTORY;

            // String aggregateOutputDirectory = ServerFile.getUserOperationDir(userName,operationName);

            // input += aggregateOutputDirectory + "\n"; // output directory for aggregate

            // String psdName = CementDatabase.getCementPSD(microstructureForm.getCementName());
            String psdName = Constants.CEMENT_PSD_FILE;
            // String psdpath = userDir.getOperationFilePath(microstructure, microstructureForm.getCement_psd());
            String psdpath = userDir.getOperationFilePath(microstruct, psdName);

            input += psdpath + "\n"; // cement PSD

            if (microstructureForm.isAdd_fine_aggregate01()) {
                input += microstructureForm.getFine_aggregate01_volfrac() + "\n";

                String gradingName = Constants.FINE_AGGREGATE_GRADING_NAME_01;
                
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getFine_aggregate01_display_name();

                input += CementDatabase.getBulkModulusOfAggregateForUser(aggregateDisplayName) + "\n";
                input += CementDatabase.getShearModulusOfAggregateForUser(aggregateDisplayName) + "\n";
            } else {
                input += "0\n";
            }

            if (microstructureForm.isAdd_fine_aggregate02()) {
                input += microstructureForm.getFine_aggregate02_volfrac() + "\n";

                String gradingName = Constants.FINE_AGGREGATE_GRADING_NAME_02;
                
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getFine_aggregate02_display_name();

                input += CementDatabase.getBulkModulusOfAggregateForUser(aggregateDisplayName) + "\n";
                input += CementDatabase.getShearModulusOfAggregateForUser(aggregateDisplayName) + "\n";
            } else {
                input += "0\n";
            }

            if (microstructureForm.isAdd_coarse_aggregate01()) {
                input += microstructureForm.getCoarse_aggregate01_volfrac() + "\n";
                String gradingName = Constants.COARSE_AGGREGATE_GRADING_NAME_01;
                
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getCoarse_aggregate01_display_name();

                input += CementDatabase.getBulkModulusOfAggregateForUser(aggregateDisplayName) + "\n";
                input += CementDatabase.getShearModulusOfAggregateForUser(aggregateDisplayName) + "\n";
            } else {
                input += "0\n";
            }

            if (microstructureForm.isAdd_coarse_aggregate02()) {
                input += microstructureForm.getCoarse_aggregate02_volfrac() + "\n";
                String gradingName = Constants.COARSE_AGGREGATE_GRADING_NAME_02;
                
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getCoarse_aggregate02_display_name();

                input += CementDatabase.getBulkModulusOfAggregateForUser(aggregateDisplayName) + "\n";
                input += CementDatabase.getShearModulusOfAggregateForUser(aggregateDisplayName) + "\n";
            } else {
                input += "0\n";
            }

            /*
            double volumeFraction = Double.parseDouble(microstructureForm.getCoarse_aggregate_volfrac());
            volumeFraction += Double.parseDouble(microstructureForm.getFine_aggregate_volfrac());

            input += volumeFraction + "\n";
             **/

            input += microstructureForm.getAir_volfrac() + "\n";
        }
        /*
        UserDirectory ud = new UserDirectory(userName);
        String[] foldersList = ud.getOperationFolderNames(this.getMicrostructure());

        boolean hasSlab = false;
        for (int i = 0; i < foldersList.length; i++) {
        if (foldersList[i].equalsIgnoreCase(Constants.AGGREGATE_FILES_DIRECTORY_NAME)) {
        hasSlab = true;
        break;
        }
        }

        String early_age = "0";
        String resolve = "0";
        if (hasSlab) {
        resolve = "1";
        }
         **/

        return input;
    }

    public String generateTransportInputForUser(String imageFileName, String outputDir, String operationName, String userName) throws SQLArgumentException, SQLException {
        // String filename = this.getMicrostructure().split("/")[1];
        String input = imageFileName + "\n";
        input += outputDir + "\n"; // output directory
        String microstruct = this.getMicrostructure();
        UserDirectory userDir = new UserDirectory(userName);

        GenerateMicrostructureForm microstructureForm = GenerateMicrostructureForm.create_from_state(microstruct, userName);
        input += outputDir + Constants.TRANSPORT_FACTOR_MAJOROUTPUT_FILE_NAME + "\n"; // fully-resolved major output file
        input += outputDir + Constants.TRANSPORT_FACTOR_RESULTS_FILE_NAME + "\n"; // fully-resolved results file
        input += outputDir + Constants.PHASE_CONTRIBUTIONS_FILE_NAME + "\n"; // fully-resolved ITZ file

        if (microstructureForm.isAdd_aggregate()) {
            // We must figure out how many sources of fine and coarse aggregate are specified
            int numFineSources = 0;
            if (microstructureForm.isAdd_fine_aggregate01()) numFineSources++;
            if (microstructureForm.isAdd_fine_aggregate02()) numFineSources++;
            int numCoarseSources = 0;
            if (microstructureForm.isAdd_coarse_aggregate01()) numCoarseSources++;
            if (microstructureForm.isAdd_coarse_aggregate02()) numCoarseSources++;
            // input += ServerFile.getUserOperationDir(userName,Constants.ELASTIC_AGGREGATE_DIRECTORY);

            // operationName = operationName + File.separator + Constants.ELASTIC_AGGREGATE_DIRECTORY;

            // String aggregateOutputDirectory = ServerFile.getUserOperationDir(userName,operationName);

            // input += aggregateOutputDirectory + "\n"; // output directory for aggregate

            // String psdName = CementDatabase.getCementPSD(microstructureForm.getCementName());
            String psdName = Constants.CEMENT_PSD_FILE;
            // String psdpath = userDir.getOperationFilePath(microstructure, microstructureForm.getCement_psd());
            String psdpath = userDir.getOperationFilePath(microstruct, psdName);

            input += psdpath + "\n"; // cement PSD

            input += Integer.toString(numFineSources) + "\n";

            if (microstructureForm.isAdd_fine_aggregate01()) {
                input += microstructureForm.getFine_aggregate01_volfrac() + "\n";

                String gradingName = microstructureForm.getFine_aggregate01_grading_name();
                if (!gradingName.endsWith(".gdg")) {
                    gradingName = gradingName + ".gdg";
                }
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getFine_aggregate01_display_name();

                input += CementDatabase.getConductivityOfAggregateForUser(aggregateDisplayName) + "\n";
            }

            if (microstructureForm.isAdd_fine_aggregate02()) {
                input += microstructureForm.getFine_aggregate02_volfrac() + "\n";

                String gradingName = microstructureForm.getFine_aggregate02_grading_name();
                if (!gradingName.endsWith(".gdg")) {
                    gradingName = gradingName + ".gdg";
                }
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getFine_aggregate02_display_name();

                input += CementDatabase.getConductivityOfAggregateForUser(aggregateDisplayName) + "\n";
            }

            input += Integer.toString(numCoarseSources) + "\n";
            if (microstructureForm.isAdd_coarse_aggregate01()) {
                input += microstructureForm.getCoarse_aggregate01_volfrac() + "\n";
                String gradingName = microstructureForm.getCoarse_aggregate01_grading_name();
                if (!gradingName.endsWith(".gdg")) {
                    gradingName = gradingName + ".gdg";
                }
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getCoarse_aggregate01_display_name();

                input += CementDatabase.getConductivityOfAggregateForUser(aggregateDisplayName) + "\n";
            }

            if (microstructureForm.isAdd_coarse_aggregate02()) {
                input += microstructureForm.getCoarse_aggregate02_volfrac() + "\n";
                String gradingName = microstructureForm.getCoarse_aggregate02_grading_name();
                if (!gradingName.endsWith(".gdg")) {
                    gradingName = gradingName + ".gdg";
                }
                String gradingPath = userDir.getOperationDir(microstruct);
                if (!gradingPath.endsWith(File.separator)) {
                    gradingPath = gradingPath + File.separator;
                }

                gradingPath = gradingPath + gradingName;

                input += gradingPath + "\n";

                String aggregateDisplayName = microstructureForm.getCoarse_aggregate02_display_name();

                input += CementDatabase.getConductivityOfAggregateForUser(aggregateDisplayName) + "\n";
            }

            /*
            double volumeFraction = Double.parseDouble(microstructureForm.getCoarse_aggregate_volfrac());
            volumeFraction += Double.parseDouble(microstructureForm.getFine_aggregate_volfrac());

            input += volumeFraction + "\n";
             **/

            input += microstructureForm.getAir_volfrac() + "\n";
        }
        return input;
    }

    /**
     * Holds value of property hydratedImagesList.
     */
    private SortedMap<String, HydratedImage> hydratedImagesList;

    /**
     * Indexed getter for property hydratedImagesList.
     * @param index Index of the property.
     * @return Value of the property for <CODE>key</CODE>.
     */
    public HydratedImage getHydratedImagesList(String key) {
        return this.hydratedImagesList.get(key);
    }

    /**
     * Getter for property hydratedImagesList.
     * @return Value of property hydratedImagesList.
     */
    public SortedMap<String, HydratedImage> getHydratedImagesList() {
        return this.hydratedImagesList;
    }

    /**
     * Setter for property hydratedImagesList.
     * @param hydratedImagesList New value of property hydratedImagesList.
     */
    public void setHydratedImagesList(SortedMap<String, HydratedImage> hydratedImagesList) {
        this.hydratedImagesList = hydratedImagesList;
    }
}
