/*
 * HydrateMixAction.java
 *
 * Created on June 20, 2007, 9:58 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.operation.hydration;

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import java.util.*;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NullMicrostructureException;
import nist.bfrl.vcctl.exceptions.NullMicrostructureFormException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.exceptions.SQLDuplicatedKeyException;
import nist.bfrl.vcctl.operation.OperationState;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import org.apache.struts.action.*;

/**
 *
 * @author mscialom
 */
public class HydrateMixAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        Map pm = request.getParameterMap();
        HttpSession session = request.getSession();
        HydrateMixForm hydrateMixForm = (HydrateMixForm) form;


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                try {
                    if (pm.containsKey("action")) {
                        String[] actions = (String[]) pm.get("action");
                        String action = actions[0];

                        if (action.equalsIgnoreCase("change_mix")) {
                            try {
                                hydrateMixForm.updateMicrostructureData(userName);
                            } catch (NullMicrostructureFormException ex) {
                                return mapping.findForward("failure");
                            } catch (NullMicrostructureException ex) {
                                return mapping.findForward("failure");
                            }
                            return mapping.findForward("mix_changed");
                        } else if (action.equalsIgnoreCase("check_hydration_name")) {
                            String hydrationName = hydrateMixForm.getOperation_name();
                            try {
                                if (!OperationDatabase.isUniqueOperationNameForUser(hydrationName, userName)) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("name_alreadyTaken");
                                    out.flush();
                                }
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            }
                            return null;
                        } else if (action.equalsIgnoreCase("check_calorimetry_file")) {
                                        
                            // Create isothermal calorimetry data file
                            String destination = ServerFile.getUserOperationDir(userName, hydrateMixForm.getOperation_name()) + Constants.CALORIMETRY_FILE;
                            try {
                                response.setContentType("text/html");
                                PrintWriter out = response.getWriter();
                                String responseText = "okay";
                                String calorimetryDataString = CementDatabase.getCalorimetryFileData(hydrateMixForm.getCalorimetry_file());
                                ArrayList<String> tokens = new ArrayList<String>();
                                Scanner tokenize = new Scanner(calorimetryDataString).useDelimiter("\\s+");
                                while (tokenize.hasNext()) {
                                    tokens.add(tokenize.next());
                                }
                                double finalTime = Double.valueOf(tokens.get(tokens.size()-2));
                                if (finalTime < 24.0) {
                                    responseText = "calFile_lessthan_24h";
                                } else if (finalTime < 48.0) {
                                    responseText = "calFile_lessthan_48h";
                                }
                                out.print(responseText);
                                out.flush();
                                return null;
                            } catch (DBFileException ex) {
                                ex.printStackTrace();
                            }
                        }

                        return mapping.findForward("failure");
                    } else {

                        // write disrealnew input file
                        String profile_name = hydrateMixForm.getProfile_name();
                        String opname = hydrateMixForm.getOperation_name();
                        String disrealnewinput;
                        try {
                            disrealnewinput = hydrateMixForm.getDisrealnew_input(userName);

                            ServerFile.writeUserOpTextFile(userName, opname, opname + ".hyd.in", disrealnewinput);
                        } catch (DBFileException ex) {
                            String dataType = ex.getType();
                            if (dataType.equalsIgnoreCase(Constants.PARAMETER_FILE_TYPE)) {
                                return mapping.findForward("empty_parameter_file");
                            } else if (dataType.equalsIgnoreCase(Constants.TIMING_OUTPUT_FILE_TYPE)) {
                                return mapping.findForward("empty_timing_output_file");
                            } else if (dataType.equalsIgnoreCase(Constants.CALORIMETRY_FILE_TYPE)) {
                                return mapping.findForward("empty_calorimetry_file");
                            } else if (dataType.equalsIgnoreCase(Constants.CHEMICAL_SHRINKAGE_FILE_TYPE)) {
                                return mapping.findForward("empty_chemical_shrinkage_file");
                            }
                            return mapping.findForward("empty_unknown_type");
                        }

                        // Get state of HydrateMicrostructureForm in XML
                        byte[] state = OperationState.save_to_Xml(hydrateMixForm);

                        // If 'save profile' is checked, then save this form's state
                        // as a hydration profile under the selected name
                        if (hydrateMixForm.isSave_profile()) {
                            HydrationProfile hp = new HydrationProfile();
                            hp.setName(profile_name);
                            hp.setState(state);
                            /*
                            try {
                            hp.save();
                            } catch (SQLException ex) {
                            ex.printStackTrace();
                            } catch (SQLArgumentException ex) {
                            ex.printStackTrace();
                            }
                             **/
                        }

                        /**************************************************************
                         *** WRITE OUT NECESSARY FILES USED BY DISREALNEW
                         **************************************************************/
                        // Copy the cement alkali characteristics file to the img directory with file name "parametersFilesDir"
                        // String source = Vcctl.getAlkaliFilesDirectory() + hydrateMixForm.getAlkali_characteristics_cement_file();
                        String alkaliCharacteristicsName = hydrateMixForm.getAlkali_characteristics_cement_file();
                        String destination = ServerFile.getUserOperationDir(userName, opname) + Constants.CEMENT_ALKALI_CHARACTERISTICS_FILE;
                        try {
                            ServerFile.writeTextFile(destination, CementDatabase.getAlkaliCharacteristicsData(alkaliCharacteristicsName));
                        } catch (SQLArgumentException ex) {
                            return mapping.findForward("incorrect_cement_alkali_characteristics_name");
                        } catch (DBFileException ex) {
                            return mapping.findForward("empty_cement_alkali_characteristics");
                        }

                        // Util.copy(source, destination);

                        // Write out the fly ash alkali characteristics file, if
                        // fly ash is present in the microstructure
                    /*
                        if (hydrateMixForm.isHas_fly_ash()) {
                        source = Vcctl.getAlkaliFilesDirectory() + hydrateMixForm.getAlkali_characteristics_fly_ash_file();
                        } else {
                        source = Vcctl.getAlkaliFilesDirectory() + Constants.NO_FLY_ASH_ALKALI_CHARACTERISTICS_FILE;
                        }
                         **/

                        if (hydrateMixForm.isHas_fly_ash()) {
                            alkaliCharacteristicsName = hydrateMixForm.getAlkali_characteristics_fly_ash_file();
                        } else {
                            alkaliCharacteristicsName = Constants.NO_FLY_ASH_ALKALI_CHARACTERISTICS_FILE;
                        }
                        destination = ServerFile.getUserOperationDir(userName, opname) + Constants.FLY_ASH_ALKALI_CHARACTERISTICS_FILE;
                        try {
                            ServerFile.writeTextFile(destination, CementDatabase.getAlkaliCharacteristicsData(alkaliCharacteristicsName));
                        } catch (SQLArgumentException ex) {
                            return mapping.findForward("incorrect_fly_ash_alkali_characteristics_name");
                        } catch (DBFileException ex) {
                            return mapping.findForward("empty_fly_ash_alkali_characteristics");
                        }
                        // Util.copy(source, destination);


                        // Write out the slag characteristics file, if slag is present in the
                        // microstructure

                        /*
                        if (hydrateMixForm.isHas_slag()) {
                        source = Vcctl.getSlagCharacteristicsFilesDirectory() + hydrateMixForm.getSlag_characteristics_file();
                        } else {
                        source = Vcctl.getSlagCharacteristicsFilesDirectory() + Constants.NO_SLAG_CHARACTERISTICS_FILE;
                        }
                         **/
                        String slagCharacteristicsName;
                        if (hydrateMixForm.isHas_slag()) {
                            slagCharacteristicsName = hydrateMixForm.getSlag_characteristics_file();
                        } else {
                            slagCharacteristicsName = Constants.NO_SLAG_CHARACTERISTICS_FILE;
                        }
                        destination = ServerFile.getUserOperationDir(userName, opname) + Constants.SLAG_CHARACTERISTICS_FILE;
                        try {
                            ServerFile.writeTextFile(destination, CementDatabase.getSlagCharacteristicsData(slagCharacteristicsName));
                        } catch (SQLArgumentException ex) {
                            return mapping.findForward("incorrect_slag_characteristics_name");
                        } catch (DBFileException ex) {
                            return mapping.findForward("empty_slag_characteristics");
                        }
                        //Util.copy(source, destination);

                        // Write out the temperature schedule file
                        if (hydrateMixForm.getThermal_conditions().equalsIgnoreCase("use schedule")) {
                            String temperature_schedule_file = hydrateMixForm.getTemperature_schedule_file();
                            /**
                             * This option is disabled in the user interface, for now
                             */
                        }

                        /**************************************************************
                         ***  END - WRITE OUT NECESSARY FILES USED BY DISREALNEW
                         **************************************************************/
                        // Create a new operation
                        Operation hydop = new Operation(opname, userName, Constants.HYDRATION_OPERATION_TYPE);

                        hydop.setState(state);
                        hydop.setDepends_on_operation_name(hydrateMixForm.getMicrostructure());
                        hydop.setDepends_on_operation_username(userName);
                        hydop.setNotes(hydrateMixForm.getNotes());
                        try {

                            // Queue the operation for execution
                            OperationDatabase.queueOperation(hydop);
                        } catch (SQLDuplicatedKeyException ex) {
                            // to-do
                            ex.printStackTrace();
                        }
                        String mstat = hydrateMixForm.getMixingStatus();
                        String fstat = Constants.OPERATION_FINISHED_STATUS;
                        if (mstat.equalsIgnoreCase(fstat)) {
                            try {
                                Thread.sleep(1000);
                            } catch (Exception ex) {}
                            return mapping.findForward("hydrating_mix");
                        } else {
                            return mapping.findForward("waiting_end_of_mix_preparation");
                        }
                    }
                } catch (SQLArgumentException ex) {
                    return (mapping.findForward("incorrect_name"));
                } catch (SQLException ex) {
                    ex.printStackTrace();
                    return mapping.findForward("database_problem");
                }
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }
}
