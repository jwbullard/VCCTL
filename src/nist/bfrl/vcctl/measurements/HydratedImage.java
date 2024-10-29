/*
 * HydratedImage.java
 *
 * Created on September 20, 2007, 2:27 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.measurements;

import java.io.File;
import java.sql.SQLException;
import nist.bfrl.vcctl.database.Operation;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;

/**
 *
 * @author mscialom
 */
public class HydratedImage {

    public HydratedImage(String name, String measurementTime, int number, String userName, String operationName) throws SQLException, SQLArgumentException {
        this.name = name;
        this.userName = userName;
        this.operationName = operationName;
        this.measurementTime = measurementTime;
        this.number = number;

        String outputElasticDirectory = Constants.ELASTIC_OPERATION_NAME_ROOT + number;
        String outputTransportDirectory = Constants.TRANSPORT_OPERATION_NAME_ROOT + number;

        String operationElasticName = operationName + File.separator + outputElasticDirectory;
        String operationTransportName = operationName + File.separator + outputTransportDirectory;

        Operation operation = OperationDatabase.getOperationForUser(operationElasticName, userName);
        String status = OperationDatabase.getOperationStatusForUser(operationElasticName, userName);
        if (operation != null) {
            String content;
            if (status.equalsIgnoreCase(Constants.OPERATION_FINISHED_STATUS)) {
                UserDirectory userDir = new UserDirectory(userName);
                String[] filesList = userDir.getOperationFileNames(operationElasticName);
                String fileName;
                for (int i = 0; i < filesList.length; i++) {
                    fileName = filesList[i];
                    if (fileName.equalsIgnoreCase(Constants.EFFECTIVE_MODULI_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationElasticName, fileName);
                        content = new String(fileBytes);
                        this.setEffectiveModuliFileContent(content);
                    } else if (fileName.equalsIgnoreCase(Constants.PHASE_CONTRIBUTIONS_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationElasticName, fileName);
                        content = new String(fileBytes);
                        this.setPhaseContributionsFileContent(content);
                    } else if (fileName.equalsIgnoreCase(Constants.ITZ_MODULI_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationElasticName, fileName);
                        content = new String(fileBytes);
                        this.setITZModuliFileContent(content);
                    } else if (fileName.equalsIgnoreCase(Constants.CONCRETE_MODULI_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationElasticName, fileName);
                        content = new String(fileBytes);
                        this.setConcreteModuliFileContent(content);
                    }
                }
            } else if (status.equalsIgnoreCase(Constants.OPERATION_RUNNING_STATUS)) {
                content = "Measuring...";
                this.setEffectiveModuliFileContent(content);
                this.setPhaseContributionsFileContent(content);
                this.setITZModuliFileContent(content);
                this.setConcreteModuliFileContent(content);
            } else if (status.equalsIgnoreCase(Constants.OPERATION_QUEUED_STATUS)) {
                content = "Waiting for hydration to complete...";
                this.setEffectiveModuliFileContent(content);
                this.setPhaseContributionsFileContent(content);
                this.setITZModuliFileContent(content);
                this.setConcreteModuliFileContent(content);
            } else if (status.equalsIgnoreCase(Constants.OPERATION_CANCELLED_STATUS) || status.equalsIgnoreCase(Constants.OPERATION_ERROR_STATUS)) {
                content = "Measurement has been cancelled.\nGo to \"My Operations\" and delete the corresponding operation if you want to measure the elastic moduli again.";
                this.setEffectiveModuliFileContent(content);
                this.setPhaseContributionsFileContent(content);
                this.setITZModuliFileContent(content);
                this.setConcreteModuliFileContent(content);
            }
        }

        operation = OperationDatabase.getOperationForUser(operationTransportName, userName);
        status = OperationDatabase.getOperationStatusForUser(operationTransportName, userName);
        if (operation != null) {
            String content;
            if (status.equalsIgnoreCase(Constants.OPERATION_FINISHED_STATUS)) {
                UserDirectory userDir = new UserDirectory(userName);
                String[] filesList = userDir.getOperationFileNames(operationTransportName);
                String fileName;
                for (int i = 0; i < filesList.length; i++) {
                    fileName = filesList[i];
                    if (fileName.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_RESULTS_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationTransportName, fileName);
                        content = new String(fileBytes);
                        this.setTransportFactorFileContent(content);
                    } else if (fileName.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_PHASE_CONTRIBUTIONS_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationTransportName, fileName);
                        content = new String(fileBytes);
                        this.setTransportPhaseContributionsFileContent(content);
                    } else if (fileName.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_ITZ_FILE_NAME)) {
                        byte[] fileBytes = ServerFile.readUserOpBinaryFile(userName, operationTransportName, fileName);
                        content = new String(fileBytes);
                        this.setTransportITZFileContent(content);
                    }
                }
            } else if (status.equalsIgnoreCase(Constants.OPERATION_RUNNING_STATUS)) {
                content = "Measuring...";
                this.setTransportFactorFileContent(content);
            } else if (status.equalsIgnoreCase(Constants.OPERATION_QUEUED_STATUS)) {
                content = "Waiting for hydration to complete...";
                this.setTransportFactorFileContent(content);
            } else if (status.equalsIgnoreCase(Constants.OPERATION_CANCELLED_STATUS) || status.equalsIgnoreCase(Constants.OPERATION_ERROR_STATUS)) {
                content = "Measurement has been cancelled.\nGo to \"My Operations\" and delete the corresponding operation if you want to measure the transport factor again.";
                this.setTransportFactorFileContent(content);
            }
        }
    }
    /**
     * Holds value of property effectiveModuliFileContent.
     */
    private String effectiveModuliFileContent;

    /**
     * Getter for property effectiveModuliFileContent.
     * @return Value of property effectiveModuliFileContent.
     */
    public String getEffectiveModuliFileContent() {
        return this.effectiveModuliFileContent;
    }

    /**
     * Setter for property effectiveModuliFileContent.
     * @param effectiveModuliFileContent New value of property effectiveModuliFileContent.
     */
    public void setEffectiveModuliFileContent(String effectiveModuliFileContent) {
        this.effectiveModuliFileContent = effectiveModuliFileContent;
    }
    /**
     * Holds value of property phaseContributionsFileContent.
     */
    private String phaseContributionsFileContent;

    /**
     * Getter for property phaseContributionsFileContent.
     * @return Value of property phaseContributionsFileContent.
     */
    public String getPhaseContributionsFileContent() {
        return this.phaseContributionsFileContent;
    }

    /**
     * Setter for property phaseContributionsFileContent.
     * @param phaseContributions New value of property phaseContributionsFileContent.
     */
    public void setPhaseContributionsFileContent(String phaseContributionsFileContent) {
        this.phaseContributionsFileContent = phaseContributionsFileContent;
    }
    /**
     * Holds value of property ITZModuliFileContent.
     */
    private String ITZModuliFileContent;

    /**
     * Getter for property ITZModuliFileContent.
     * @return Value of property ITZModuliFileContent.
     */
    public String getITZModuliFileContent() {
        return this.ITZModuliFileContent;
    }

    /**
     * Setter for property ITZModuliFileContent.
     * @param ITZModuliFileContent New value of property ITZModuliFileContent.
     */
    public void setITZModuliFileContent(String ITZModuliFileContent) {
        this.ITZModuliFileContent = ITZModuliFileContent;
    }

    /**
     * Holds value of property ConcreteModuliFileContent.
     */
    private String ConcreteModuliFileContent;

    /**
     * Getter for property ConcreteModuliFileContent.
     * @return Value of property ConcreteModuliFileContent.
     */
    public String getConcreteModuliFileContent() {
        return this.ConcreteModuliFileContent;
    }

    /**
     * Setter for property ConcreteModuliFileContent.
     * @param ConcreteModuliFileContent New value of property ConcreteModuliFileContent.
     */
    public void setConcreteModuliFileContent(String ConcreteModuliFileContent) {
        this.ConcreteModuliFileContent = ConcreteModuliFileContent;
    }

    /**
     * Holds value of property transportFactorFileContent.
     */
    private String transportFactorFileContent;

    /**
     * Getter for property transportFactorFileContent.
     * @return Value of property transportFactorFileContent.
     */
    public String getTransportFactorFileContent() {
        return this.transportFactorFileContent;
    }

    /**
     * Setter for property transportFactorFileContent.
     * @param transportFactorFileContent New value of property transportFactorFileContent.
     */
    public void setTransportFactorFileContent(String TransportFactorFileContent) {
        this.transportFactorFileContent = TransportFactorFileContent;
    }

     /**
     * Holds value of property transportPhaseContributionsFileContent.
     */
    private String transportPhaseContributionsFileContent;

    /**
     * Getter for property transportPhaseContributionsFileContent.
     * @return Value of property transportPhaseContributionsFileContent.
     */
    public String getTransportPhaseContributionsFileContent() {
        return this.transportPhaseContributionsFileContent;
    }

    /**
     * Setter for property transportPhaseContributionsFileContent.
     * @param transportPhaseContributionsFileContent New value of property transportPhaseContributionsFileContent.
     */
    public void setTransportPhaseContributionsFileContent(String TransportPhaseContributionsFileContent) {
        this.transportPhaseContributionsFileContent = TransportPhaseContributionsFileContent;
    }

         /**
     * Holds value of property transportITZFileContent.
     */
    private String transportITZFileContent;

    /**
     * Getter for property transportITZFileContent.
     * @return Value of property transportITZFileContent.
     */
    public String getTransportITZFileContent() {
        return this.transportITZFileContent;
    }

    /**
     * Setter for property transportITZFileContent.
     * @param transportITZFileContent New value of property transportITZFileContent.
     */
    public void setTransportITZFileContent(String TransportITZFileContent) {
        this.transportITZFileContent = TransportITZFileContent;
    }

    /**
     * Holds value of property name.
     */
    private String name;

    /**
     * Getter for property name.
     * @return Value of property name.
     */
    public String getName() {
        return this.name;
    }

    /**
     * Setter for property name.
     * @param name New value of property name.
     */
    public void setName(String name) {
        this.name = name;
    }
    /**
     * Holds value of property userName.
     */
    private String userName;

    /**
     * Getter for property userName.
     * @return Value of property userName.
     */
    public String getUserName() {
        return this.userName;
    }

    /**
     * Setter for property userName.
     * @param userName New value of property userName.
     */
    public void setUserName(String userName) {
        this.userName = userName;
    }
    /**
     * Holds value of property operationName.
     */
    private String operationName;

    /**
     * Getter for property operationName.
     * @return Value of property operationName.
     */
    public String getOperationName() {
        return this.operationName;
    }

    /**
     * Setter for property operationName.
     * @param operationName New value of property operationName.
     */
    public void setOperationName(String operationName) {
        this.operationName = operationName;
    }
    /**
     * Holds value of property elasticModuliMeasurementsDone.
     */
    private boolean elasticModuliMeasurementsDone;

    /**
     * Getter for property elasticModuliMeasurementsDone.
     * @return Value of property elasticModuliMeasurementsDone.
     */
    public boolean isElasticModuliMeasurementsDone() {
        return this.elasticModuliMeasurementsDone;
    }

    /**
     * Setter for property elasticModuliMeasurementsDone.
     * @param elasticModuliMeasurementsDone New value of property elasticModuliMeasurementsDone.
     */
    public void setElasticModuliMeasurementsDone(boolean elasticModuliMeasurementsDone) {
        this.elasticModuliMeasurementsDone = elasticModuliMeasurementsDone;
    }
    /**
     * Holds value of property measurementTime.
     */
    private String measurementTime;

    /**
     * Getter for property measurementTime.
     * @return Value of property measurementTime.
     */
    public String getMeasurementTime() {
        return this.measurementTime;
    }

    /**
     * Setter for property measurementTime.
     * @param measurementTime New value of property measurementTime.
     */
    public void setMeasurementTime(String measurementTime) {
        this.measurementTime = measurementTime;
    }
    /**
     * Holds value of property number.
     */
    private int number;

    /**
     * Getter for property number.
     * @return Value of property number.
     */
    public int getNumber() {
        return this.number;
    }

    /**
     * Setter for property number.
     * @param number New value of property number.
     */
    public void setNumber(int number) {
        this.number = number;
    }
}
