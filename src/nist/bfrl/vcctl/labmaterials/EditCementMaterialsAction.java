/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import javax.servlet.http.*;
import java.util.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoCementException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.DefaultNameBuilder;
import nist.bfrl.vcctl.util.FileTypes;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class EditCementMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        CementMaterialsForm cementMaterialsForm = (CementMaterialsForm) form;

        String action = request.getParameter("action");
        String cemName;

        if (action != null) {
            try {
                if (action.equalsIgnoreCase("change_cement")) {

                    String name = cementMaterialsForm.getCement().getName();

                    Cement cement = null;
                    if (name == null || name.equalsIgnoreCase("")) {
                        cement = new Cement();
                    } else {
                        cement = Cement.load(name);
                    }

                    cementMaterialsForm.setCement(cement);
                    cemName = cement.getName();
                    request.setAttribute("cemName", cemName);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("upload")) {

                    FormFile ff = cementMaterialsForm.getUploaded_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Cement cement = cementMaterialsForm.getCement();
                    try {
                        CementUploadResult cementUploadResult = UploadFileHandler.uploadCementZIPFile(ff, cement);
                        HttpSession session = request.getSession();
                        session.setAttribute("psdDataText", cementUploadResult.getPsdDataText());
                        session.setAttribute("alkaliDataText", cementUploadResult.getAlkaliDataText());
                        // cement = cementUploadResult.getCement();
                        // labMaterialsForm.setCement(cement);

                        if (cementUploadResult.isPsdNameAlreadyTaken() || cementUploadResult.isAlkaliNameAlreadyTaken()) {
                            // The user attempted to upload a cement containing a PSD or an alkali that already exists in the database
                            PrintWriter out;
                            String name, type, message;

                            String JSONResponse = "{ \"existingFiles\": [";
                            if (cementUploadResult.isPsdNameAlreadyTaken()) {
                                name = cementUploadResult.getPsdName();
                                type = FileTypes.typeDescription(Constants.PSD_TYPE);
                                message = "There already is a psd called \\\"" + name + "\\\" in the database.";
                                String newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, name, "");
                                JSONResponse += "{ \"type\": \"" + type + "\", \"name\": \"" + name + "\", \"message\": \"" +
                                        message + "\", \"newName\": \"" + newName + "\" }, ";
                            }
                            if (cementUploadResult.isAlkaliNameAlreadyTaken()) {
                                name = cementUploadResult.getAlkaliName();
                                type = FileTypes.typeDescription(Constants.ALKALI_CHARACTERISTICS_TYPE);
                                message = "There already is an alkali called \\\"" + name + "\\\" in the database.";
                                String newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, name, "");
                                JSONResponse += "{ \"type\": \"" + type + "\", \"name\": \"" + name + "\", \"message\": \"" +
                                        message + "\", \"newName\": \"" + newName + "\" }";
                            }
                            if (JSONResponse.endsWith(", ")) {
                                // if only the PSD already exists in the database, remove the ", " we added previously
                                JSONResponse = JSONResponse.substring(0, JSONResponse.length() - 2);
                            }
                            JSONResponse += "]}";
                            response.setContentType("text/html");
                            out = response.getWriter();
                            out.print(JSONResponse);
                            out.flush();
                            return null;
                        }

                    } catch (FileNotFoundException ex) {
                        ex.printStackTrace();
                    } catch (IOException ex) {
                        ex.printStackTrace();
                    }

                    if (cement != null) {
                        cementMaterialsForm.setUploaded_file(null);
                        return mapping.findForward("cement_uploaded");
                    } else {
                        return mapping.findForward("cement_not_uploaded");
                    }

                } else if (action.equalsIgnoreCase("use_existing_psd_or_alkali")) {
                    // The user attempted to upload a cement containing a PSD AND alkali that already exist in the database
                    // and chose to use the existing one.
                    // In that case, nothing to do because the PSD and alkali name have already been set to the right one previously
                    return mapping.findForward("cement_uploaded");

                } else if (action.equalsIgnoreCase("create_new_psd_or_alkali")) {
                    Cement cement = cementMaterialsForm.getCement();
                    String psdName = request.getParameter("psdName");
                    String alkaliName = request.getParameter("alkaliName");
                    HttpSession session = request.getSession();
                    boolean psdSaved = false;
                    boolean alkaliSaved = false;

                    if (psdName != null && !psdName.equalsIgnoreCase("")) {
                        if (CementDatabase.isUniqueDBFileName(psdName)) {
                            // Verify that there isn't a DBFile with the same name
                            DBFile psd = new DBFile(psdName, Constants.PSD_TYPE, (String) session.getAttribute("psdDataText"));
                            psd.saveFromStrings();
                            psdSaved = true;
                            cement.setPsd(psdName);
                        }
                    } else {
                        psdSaved = true;
                    }

                    if (alkaliName != null && !alkaliName.equalsIgnoreCase("")) {
                        if (CementDatabase.isUniqueDBFileName(alkaliName)) {
                            // Verify that there isn't a DBFile with the same name
                            DBFile alkali = new DBFile(alkaliName, Constants.ALKALI_CHARACTERISTICS_TYPE, (String) session.getAttribute("alkaliDataText"));
                            alkali.saveFromStrings();
                            alkaliSaved = true;
                            cement.setAlkaliFile(alkaliName);
                        }
                    } else {
                        alkaliSaved = true;
                    }

                    if (!psdSaved || !alkaliSaved) {
                        // The user attempted to upload a cement containing a PSD or an alkali that already exists in the database
                        PrintWriter out;
                        String type, message;

                        String JSONResponse = "{ \"existingFiles\": [";
                        if (!psdSaved) {
                            cement.setPsd(psdName);
                            type = FileTypes.typeDescription(Constants.PSD_TYPE);
                            message = "There already is a psd called \\\"" + psdName + "\\\" in the database.";
                            String newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, psdName, "");
                            JSONResponse += "{ \"type\": \"" + type + "\", \"name\": \"" + psdName + "\", \"message\": \"" +
                                    message + "\", \"newName\": \"" + newName + "\" }, ";
                        }
                        if (!alkaliSaved) {
                            cement.setAlkaliFile(alkaliName);
                            type = FileTypes.typeDescription(Constants.ALKALI_CHARACTERISTICS_TYPE);
                            message = "There already is an alkali called \\\"" + alkaliName + "\\\" in the database.";
                            String newName = DefaultNameBuilder.buildDefaultMaterialName(Constants.DB_FILE_TABLE_NAME, alkaliName, "");
                            JSONResponse += "{ \"type\": \"" + type + "\", \"name\": \"" + alkaliName + "\", \"message\": \"" +
                                    message + "\", \"newName\": \"" + newName + "\" }";
                        }
                        if (JSONResponse.endsWith(", ")) {
                            // if only the PSD already exists in the database, remove the ", " we added previously
                            JSONResponse = JSONResponse.substring(0, JSONResponse.length() - 2);
                        }
                        JSONResponse += "]}";
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print(JSONResponse);
                        out.flush();
                        return null;
                    }

                    return mapping.findForward("cement_uploaded");


                } else if (action.equalsIgnoreCase("save_cement")) {
                    Cement cement = cementMaterialsForm.getCement();
                    try {
                        cement.saveFromStrings();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_cement");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_cement_as")) {
                    Cement cement = cementMaterialsForm.getCement();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueCementName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("cement_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    cement.setName(name);
                    try {
                        cement.saveAsFromStrings();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_cement");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("new_cement")) {
                    Cement cement = new Cement();
                    cementMaterialsForm.setCement(cement);
                    cemName = "newCement";
                    request.setAttribute("cemName", cemName);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_cement")) {
                    Cement cement = cementMaterialsForm.getCement();
                    try {
                        cement.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_cement");
                        out.flush();
                        return null;
                    }

                    try {
                        cement = Cement.load(Constants.DEFAULT_CEMENT);
                        cementMaterialsForm.setCement(cement);
                        cemName = cement.getName();
                        request.setAttribute("cemName", cemName);

                    } catch (SQLArgumentException ex) {
                        try {
                            cement = Cement.load(CementDatabase.getFirstCementName());
                            cementMaterialsForm.setCement(cement);
                            cemName = cement.getName();
                            request.setAttribute("cemName", cemName);
                        } catch (NoCementException exc) {
                            return (mapping.findForward("no_cement"));
                        }
                        ex.printStackTrace();
                    }
                    return (mapping.findForward("success"));

                } else if (action.equalsIgnoreCase("new_cement_data_file")) {
                    String type = cementMaterialsForm.getCementDataFile().getType();
                    DBFile cementDataFile = new DBFile(type);
                    cementMaterialsForm.setCementDataFile(cementDataFile);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_cement_data_file")) {

                    String name = cementMaterialsForm.getCementDataFile().getName();

                    DBFile cementDataFile;
                    if (name == null || name.equalsIgnoreCase("")) {
                        String type = cementMaterialsForm.getCementDataFile().getType();
                        cementDataFile = new DBFile(type);
                    } else {
                        cementDataFile = DBFile.load(name);
                        cementMaterialsForm.setCementDataFile(cementDataFile);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_cement_data_file")) {
                    DBFile cementDataFile = cementMaterialsForm.getCementDataFile();
                    String type = cementDataFile.getType();
                    String responseText = "success";
                    PrintWriter out = response.getWriter();
                    response.setContentType("text/html");
                    try {
                        cementDataFile.saveFromStrings();
                    } catch (SQLException ex) {
                        responseText = "problem_when_saving_cement_data_file";
                        out.print(responseText);
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_cement_data_file_as")) {
                    DBFile cementDataFile = cementMaterialsForm.getCementDataFile();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueDBFileName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("cement_data_file_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    cementDataFile.setName(name);
                    try {
                        cementDataFile.saveFromStrings();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_cement_data_file");
                        out.flush();
                        return null;
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_cement_data_file")) {
                    DBFile dbFile = cementMaterialsForm.getCementDataFile();
                    try {
                        dbFile.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_cement_data_file");
                        out.flush();
                        return null;
                    }

                    try {
                        dbFile = DBFile.load(CementDatabase.getFirstCementDataFileName());
                        cementMaterialsForm.setCementDataFile(dbFile);
                    } catch (DBFileException ex) {
                        return (mapping.findForward("no_cement_data_file"));
                    }
                    return (mapping.findForward("success"));


                }
            } catch (SQLArgumentException ex) {
                return (mapping.findForward("incorrect_name"));
            } catch (SQLException ex) {
                return mapping.findForward("database_problem");
            } catch (IOException ex) {
                ex.printStackTrace();
            }

            return (mapping.findForward("failure"));
        }
        return (mapping.findForward("success"));
    }
}
