/*
 * PrepareMixAction.java
 *
 * Created on 1 février 2007, 14:22
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.operation.microstructure;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import java.text.ParseException;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.PSDTooSmallException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.exceptions.SQLDuplicatedKeyException;
import nist.bfrl.vcctl.operation.OperationState;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import org.apache.struts.action.*;
import nist.bfrl.vcctl.util.UserDirectory;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.*;

/**
 *
 * @author mscialom
 */
public class PrepareMixAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        Map pm = request.getParameterMap();
        HttpSession session = request.getSession();
        GenerateMicrostructureForm microstructureForm = (GenerateMicrostructureForm) form;


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {

                try {
                    if (pm.containsKey("action")) {
                        String[] actions = (String[]) pm.get("action");
                        String action = actions[0];

                        if (action.equalsIgnoreCase("change_cement")) {
                            // String selectedCement = microstructureForm.getCement_psd();
                            String selectedCement = microstructureForm.getCementName();
                            try {
                                microstructureForm.updateFractions();
                                microstructureForm.updateSulfateFractionsGivenCement(selectedCement);
                                microstructureForm.updateMixVolumeFractions();
                            } catch (ParseException ex) {
                                ex.printStackTrace();
                            }

                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_flyash")) {
                            try {
                                microstructureForm.updateFlyAshSpecificGravity();
                            } catch (DBFileException ex) {
                                if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                                    return (mapping.findForward("no_psd"));
                                }
                            }

                            if (microstructureForm.get_fly_ash_massfrac() > 0.0) {
                                try {
                                    microstructureForm.calculateVolumeFractionsGivenMassFractions();
                                } catch (ParseException ex) {
                                    ex.printStackTrace();
                                }
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_slag")) {
                            try {
                                microstructureForm.updateSlagSpecificGravity();
                            } catch (DBFileException ex) {
                                if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                                    return (mapping.findForward("no_psd"));
                                }
                            }

                            if (microstructureForm.get_slag_massfrac() > 0.0) {
                                try {
                                    microstructureForm.calculateVolumeFractionsGivenMassFractions();
                                } catch (ParseException ex) {
                                    ex.printStackTrace();
                                }
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_filler")) {
                            try {
                                microstructureForm.updateInertFillerSpecificGravity();
                            } catch (DBFileException ex) {
                                if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                                    return (mapping.findForward("no_psd"));
                                }
                            }

                            if (microstructureForm.get_inert_filler_massfrac() > 0.0) {
                                try {
                                    microstructureForm.calculateVolumeFractionsGivenMassFractions();
                                } catch (ParseException pex) {
                                    pex.printStackTrace();
                                }
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_coarse_aggregate01")) {
                            try {
                                microstructureForm.updateCoarseAggregate01();
                            } catch (SQLArgumentException sqlex) {
                                return mapping.findForward("incorrect_coarse_aggregate_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_coarse_aggregate02")) {
                            try {
                                microstructureForm.updateCoarseAggregate02();
                            } catch (SQLArgumentException sqlex) {
                                return mapping.findForward("incorrect_coarse_aggregate_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_fine_aggregate01")) {
                            try {
                                microstructureForm.updateFineAggregate01();
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_name");
                            } catch (ParseException pex) {
                                System.err.println("Parse exception for type double");
                            }
                            return mapping.findForward("change_made");
                        } else if (action.equalsIgnoreCase("change_fine_aggregate02")) {
                            try {
                                microstructureForm.updateFineAggregate02();
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_name");
                            } catch (ParseException pex) {
                                System.err.println("Parse exception for type double");
                            }
                            return mapping.findForward("change_made");

                        } else if (action.equalsIgnoreCase("check_coarse_aggregate01_grading")) {
                            try {
                                if (!microstructureForm.checkCoarseAggregate01Grading()) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("grading.not-compatible-with-system-size");
                                    out.flush();
                                    return null;
                                }
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_coarse_aggregate_grading_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                        } else if (action.equalsIgnoreCase("check_coarse_aggregate02_grading")) {
                            try {
                                if (!microstructureForm.checkCoarseAggregate02Grading()) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("grading.not-compatible-with-system-size");
                                    out.flush();
                                    return null;
                                }
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_coarse_aggregate_grading_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }

                        } else if (action.equalsIgnoreCase("change_coarse_aggregate01_grading")) {
                            String selectedCoarseAggregateGrading = microstructureForm.getCoarse_aggregate01_grading_name();
                            try {
                                if (microstructureForm.updateCoarseAggregate01Grading()) {
                                    return mapping.findForward("change_made");
                                } else {
                                    ActionMessages errors = new ActionMessages();
                                    errors.add("coarse-grading.not-compatible-with-system-size", new ActionMessage("grading.not-compatible-with-system-size", microstructureForm.getCoarse_aggregate01_grading_name()));
                                    this.saveErrors(request, errors);
                                    return mapping.findForward("change_not_made");
                                }
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                        } else if (action.equalsIgnoreCase("change_coarse_aggregate02_grading")) {
                            String selectedCoarseAggregateGrading = microstructureForm.getCoarse_aggregate02_grading_name();
                            try {
                                if (microstructureForm.updateCoarseAggregate02Grading()) {
                                    return mapping.findForward("change_made");
                                } else {
                                    ActionMessages errors = new ActionMessages();
                                    errors.add("coarse-grading.not-compatible-with-system-size", new ActionMessage("grading.not-compatible-with-system-size", microstructureForm.getCoarse_aggregate02_grading_name()));
                                    this.saveErrors(request, errors);
                                    return mapping.findForward("change_not_made");
                                }
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }

                        } else if (action.equalsIgnoreCase("check_fine_aggregate01_grading")) {
                            try {
                                if (!microstructureForm.checkFineAggregate01Grading()) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("grading.not-compatible-with-system-size");
                                    out.flush();
                                    return null;
                                }
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_grading_name");
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                        } else if (action.equalsIgnoreCase("check_fine_aggregate02_grading")) {
                            try {
                                if (!microstructureForm.checkFineAggregate02Grading()) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("grading.not-compatible-with-system-size");
                                    out.flush();
                                    return null;
                                }
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_grading_name");
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }

                        } else if (action.equalsIgnoreCase("change_fine_aggregate01_grading")) {
                            String selectedFineAggregateGrading = microstructureForm.getFine_aggregate01_grading_name();
                            try {
                                if (microstructureForm.updateFineAggregate01Grading()) {
                                    return mapping.findForward("change_made");
                                } else {
                                    ActionMessages errors = new ActionMessages();
                                    errors.add("fine-grading.not-compatible-with-system-size", new ActionMessage("grading.not-compatible-with-system-size", microstructureForm.getFine_aggregate01_grading_name()));
                                    this.saveErrors(request, errors);
                                    return mapping.findForward("change_not_made");
                                }
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_grading_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                        } else if (action.equalsIgnoreCase("change_fine_aggregate02_grading")) {
                            String selectedFineAggregateGrading = microstructureForm.getFine_aggregate02_grading_name();
                            try {
                                if (microstructureForm.updateFineAggregate02Grading()) {
                                    return mapping.findForward("change_made");
                                } else {
                                    ActionMessages errors = new ActionMessages();
                                    errors.add("fine-grading.not-compatible-with-system-size", new ActionMessage("grading.not-compatible-with-system-size", microstructureForm.getFine_aggregate02_grading_name()));
                                    this.saveErrors(request, errors);
                                    return mapping.findForward("change_not_made");
                                }
                            } catch (SQLArgumentException ex) {
                                return mapping.findForward("incorrect_fine_aggregate_grading_name");
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }

                        } else if (action.equalsIgnoreCase("save_coarse_aggregate01_grading")) {
                            try {
                                microstructureForm.saveNewCoarse01Grading();
                            } catch (SQLDuplicatedKeyException ex) {
                                // to-do
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("aggregate_saved");
                        } else if (action.equalsIgnoreCase("save_fine_aggregate01_grading")) {
                            try {
                                microstructureForm.saveNewFine01Grading();
                            } catch (SQLDuplicatedKeyException ex) {
                                // to-do
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("aggregate_saved");
                        } else if (action.equalsIgnoreCase("save_coarse_aggregate02_grading")) {
                            try {
                                microstructureForm.saveNewCoarse02Grading();
                            } catch (SQLDuplicatedKeyException ex) {
                                // to-do
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("aggregate_saved");
                        } else if (action.equalsIgnoreCase("save_fine_aggregate02_grading")) {
                            try {
                                microstructureForm.saveNewFine02Grading();
                            } catch (SQLDuplicatedKeyException ex) {
                                // to-do
                                ex.printStackTrace();
                            } catch (ParseException pex) {
                                pex.printStackTrace();
                            }
                            return mapping.findForward("aggregate_saved");

                        } else if (action.equalsIgnoreCase("check_mix_name")) {
                            String mixName = microstructureForm.getMix_name();
                            try {
                                if (!OperationDatabase.isUniqueOperationNameForUser(mixName, userName)) {
                                    response.setContentType("text/html");
                                    PrintWriter out = response.getWriter();
                                    out.print("name_alreadyTaken");
                                    out.flush();
                                }
                            } catch (IOException ex) {
                                ex.printStackTrace();
                            }
                            return null;
                        }

                        return mapping.findForward("failure");
                    } else {

                        String mixName = microstructureForm.getMix_name();
                        String opname = mixName;
                        /*
                        if (mixName.indexOf(".img") < 0) {
                        mixName += ".img";
                        }
                        microstructureForm.setMix_name(mixName)
                         **/

                        if (!OperationDatabase.isUniqueOperationNameForUser(mixName, userName)) {
                            ActionMessages errors = new ActionMessages();
                            errors.add("alreadyused", new ActionMessage("name.already-used", mixName));
                            this.saveErrors(request, errors);

                            return (mapping.findForward("name_already_used"));
                        }

                        InitialMicrostructure initmicro = new InitialMicrostructure(userName);
                        boolean params_ok;
                        try {
                            params_ok = initmicro.setParameters(microstructureForm);

                            if (!params_ok) {
                                return mapping.findForward("failure");
                            }
                        } catch (PSDTooSmallException ex) {
                            return (mapping.findForward("psd_too_small"));
                        } catch (DBFileException ex) {
                            String dataType = ex.getType();
                            if (dataType.equalsIgnoreCase(Constants.PSD_TYPE)) {
                                return (mapping.findForward("empty_psd"));
                            }
                            return (mapping.findForward("empty_unknown_type"));
                        }

                        // session.setAttribute("initmicro", initmicro);

                        // initmicro = (InitialMicrostructure)session.getAttribute("initmicro");\

                        // Save the psd file to disk on the server
                        // UserDirectory ud = UserDirectory.INSTANCE;
                        UserDirectory userDir = new UserDirectory(userName);
                        // String psdname = initmicro.getDistribute_clinker_phases_psd();
                        // String psdname = initmicro.getCement_psd();
                        // String psdpath = userDir.getOperationFilePath(opname, psdname);

                        String psdname = initmicro.getDistribute_clinker_phases_psd();
                        // String psdpath = userDir.getOperationFilePath(opname, psdname);
                        String directoryPath = userDir.getOperationDir(opname);

                        try {
                            DistributeClinkerPhases.openCorrelationFiles(psdname, directoryPath);
                        } catch (SQLArgumentException ex) {
                            return mapping.findForward("incorrect_cement_name");
                        }

                        // initmicro.create_genpartrun_input();

                        // Create a new operation
                        Operation microop = new Operation(opname, userName, Constants.MICROSTUCTURE_OPERATION_TYPE);

                        byte[] microopState = OperationState.save_to_Xml(microstructureForm);
                        microop.setState(microopState);
                        microop.setDepends_on_operation_name("");
                        microop.setDepends_on_operation_username(userName);
                        String notes = initmicro.getNotes();
                        microop.setNotes(notes);

                        // Write out input file and dissolution bias file
                        //  initmicro.create_genpartrun_input();
                        initmicro.create_genpartrun_input3();
                        String intext = initmicro.getGenpartrun_input();
                        ServerFile.writeUserOpTextFile(userName, opname, opname + ".img.in", intext);
                        String biasinfo = initmicro.get_bias_info();
                        ServerFile.writeUserOpTextFile(userName, opname, opname + ".bias", biasinfo);

                        try {
                            OperationDatabase.queueOperation(microop);
                        } catch (SQLDuplicatedKeyException ex) {
                            // to-do
                            ex.printStackTrace();
                        }
                        session.setAttribute("bmoinput", intext);

                        session.setAttribute("initmicro", initmicro);

                        if (microstructureForm.isAdd_aggregate() && (initmicro.getCoarse_aggregate01_mass_fraction() > 0 || initmicro.getCoarse_aggregate02_mass_fraction() > 0 || initmicro.getFine_aggregate01_mass_fraction() > 0 || initmicro.getFine_aggregate02_mass_fraction() > 0)) {
                            if (microstructureForm.isUse_visualize_concrete()) {
                                String genAggOpName = opname + File.separator + Constants.AGGREGATE_FILES_DIRECTORY_NAME;
                                // String genAggOpName = opname + "/" + Constants.AGGREGATE_FILES_DIRECTORY_NAME;

                                // Create a new operation
                                Operation genAggOp = new Operation(genAggOpName, userName, Constants.AGGREGATE_OPERATION_TYPE);

                                genAggOp.setDepends_on_operation_name("");
                                genAggOp.setDepends_on_operation_username(userName);
                                notes = initmicro.getNotes();
                                genAggOp.setNotes(notes);

                                // Write out input file for genaggpack
                                initmicro.createGenaggpackInput();
                                intext = initmicro.getGenaggpackInput();
                                ServerFile.writeUserOpTextFile(userName, genAggOpName, Constants.GENAGGPACK_INPUT_FILE, intext);

                                try {
                                    OperationDatabase.queueOperation(genAggOp);
                                } catch (SQLDuplicatedKeyException ex) {
                                    // to-do
                                    ex.printStackTrace();
                                }
                            }
                        }
                        return mapping.findForward("generating_microstructure");
                    }
                } catch (SQLArgumentException ex) {
                    return mapping.findForward("incorrect_cement_name");
                } catch (SQLException ex) {
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
