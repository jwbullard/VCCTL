/*
 * EditLabMaterialsAction.java
 *
 * Created on May 6, 2005, 11:56 AM
 */
package nist.bfrl.vcctl.labmaterials;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoCementException;
import nist.bfrl.vcctl.exceptions.NoFlyAshException;
import nist.bfrl.vcctl.exceptions.NoInertFillerException;
import nist.bfrl.vcctl.exceptions.NoSlagException;
import nist.bfrl.vcctl.exceptions.NoCoarseAggregateException;
import nist.bfrl.vcctl.exceptions.NoFineAggregateException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.DefaultNameBuilder;
import nist.bfrl.vcctl.util.FileTypes;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author tahall
 */
public final class EditLabMaterialsAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        LabMaterialsForm labMaterialsForm = (LabMaterialsForm) form;

        String action = request.getParameter("action");

        if (action != null) {
            try {
                if (action.equalsIgnoreCase("change_cement")) {

                    String name = labMaterialsForm.getCement().getName();

                    Cement cement = null;
                    if (name == null || name.equalsIgnoreCase("")) {
                        cement = new Cement();
                    } else {
                        cement = Cement.load(name);
                    }
                    
                    labMaterialsForm.setCement(cement);
                    labMaterialsForm.setCemName(cement);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("upload")) {

                    FormFile ff = labMaterialsForm.getUploaded_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Cement cement = labMaterialsForm.getCement();
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
                        labMaterialsForm.setUploaded_file(null);
                        return mapping.findForward("cement_uploaded");
                    } else {
                        return mapping.findForward("cement_not_uploaded");
                    }

                } else if (action.equalsIgnoreCase("upload_coarse_aggregate")) {

                    FormFile ff = labMaterialsForm.getUploaded_coarse_aggregate_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Aggregate coarse_aggregate = labMaterialsForm.getCoarseAggregate();
                    try {
                        AggregateUploadResult aggregateUploadResult = UploadFileHandler.uploadAggregateZIPFile(ff, coarse_aggregate);
                        HttpSession session = request.getSession();
                        if (aggregateUploadResult.getShapeZIPFilePresent()) {
                            // The user attempted to upload an aggregate containing no shape folder
                            PrintWriter out;
                            String name, type, message;

                            String JSONResponse = "{ \"noShapeFiles\": [";
                            message = "There is no zipped shape folder in this upload.";
                            JSONResponse += "{ \"message\": \"" + message + "\" }";

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

                    if (coarse_aggregate != null) {
                        labMaterialsForm.setUploaded_coarse_aggregate_file(null);
                        return mapping.findForward("coarse_aggregate_uploaded");
                    } else {
                        return mapping.findForward("coarse_aggregate_not_uploaded");
                    }

                } else if (action.equalsIgnoreCase("upload_fine_aggregate")) {

                    FormFile ff = labMaterialsForm.getUploaded_fine_aggregate_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Aggregate fine_aggregate = labMaterialsForm.getFineAggregate();
                    try {
                        AggregateUploadResult aggregateUploadResult = UploadFileHandler.uploadAggregateZIPFile(ff, fine_aggregate);
                        HttpSession session = request.getSession();
                        if (aggregateUploadResult.getShapeZIPFilePresent()) {
                            // The user attempted to upload an aggregate containing no shape folder
                            PrintWriter out;
                            String name, type, message;

                            String JSONResponse = "{ \"noShapeFiles\": [";
                            message = "There is no zipped shape folder in this upload.";
                            JSONResponse += "{ \"message\": \"" + message + "\" }";

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

                    if (fine_aggregate != null) {
                        labMaterialsForm.setUploaded_fine_aggregate_file(null);
                        return mapping.findForward("fine_aggregate_uploaded");
                    } else {
                        return mapping.findForward("fine_aggregate_not_uploaded");
                    }
 // TO HERE
                } else if (action.equalsIgnoreCase("use_existing_psd_or_alkali")) {
                    // The user attempted to upload a cement containing a PSD AND alkali that already exist in the database
                    // and chose to use the existing one.
                    // In that case, nothing to do because the PSD and alkali name have already been set to the right one previously
                    return mapping.findForward("cement_uploaded");

                } else if (action.equalsIgnoreCase("create_new_psd_or_alkali")) {
                    Cement cement = labMaterialsForm.getCement();
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
                    Cement cement = labMaterialsForm.getCement();
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
                    Cement cement = labMaterialsForm.getCement();

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
                    labMaterialsForm.setCement(cement);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_cement")) {
                    Cement cement = labMaterialsForm.getCement();
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
                        labMaterialsForm.setCement(cement);
                    } catch (SQLArgumentException ex) {
                        try {
                            cement = Cement.load(CementDatabase.getFirstCementName());
                            labMaterialsForm.setCement(cement);
                        } catch (NoCementException exc) {
                            return (mapping.findForward("no_cement"));
                        }
                        ex.printStackTrace();
                    }
                    return (mapping.findForward("success"));

                } else if (action.equalsIgnoreCase("change_coarse_aggregate")) {

                    String name = labMaterialsForm.getCoarseAggregate().getName();

                    Aggregate coarseAggregate;
                    if (name == null || name.equalsIgnoreCase("")) {
                        coarseAggregate = new Aggregate();
                    } else {
                        coarseAggregate = Aggregate.load(name);
                        labMaterialsForm.setCoarseAggregate(coarseAggregate);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_coarse_aggregate")) {
                    Aggregate coarseAggregate = labMaterialsForm.getCoarseAggregate();
                    try {
                        coarseAggregate.save();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_coarse_aggregate");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_coarse_aggregate_as")) {
                    Aggregate coarseAggregate = labMaterialsForm.getCoarseAggregate();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueAggregateName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("coarse_aggregate_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    coarseAggregate.setName(name);
                    try {
                        coarseAggregate.saveAs();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_coarse_aggregate");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("new_coarse_aggregate")) {
                    Aggregate coarseAggregate = new Aggregate();
                    labMaterialsForm.setCoarseAggregate(coarseAggregate);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_coarse_aggregate_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_coarse_aggregate")) {
                    Aggregate coarseAggregate = labMaterialsForm.getCoarseAggregate();
                    try {
                        coarseAggregate.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_cement");
                        out.flush();
                        return null;
                    }

                    try {
                        coarseAggregate = Aggregate.load(CementDatabase.getFirstCoarseAggregateName());
                        labMaterialsForm.setCoarseAggregate(coarseAggregate);
                    } catch (NoCoarseAggregateException ex) {
                        return (mapping.findForward("no_coarse_aggregate"));
                    }
                    return (mapping.findForward("success"));

                } else if (action.equalsIgnoreCase("change_fine_aggregate")) {

                    String name = labMaterialsForm.getFineAggregate().getName();

                    Aggregate fineAggregate;
                    if (name == null || name.equalsIgnoreCase("")) {
                        fineAggregate = new Aggregate();
                    } else {
                        fineAggregate = Aggregate.load(name);
                        labMaterialsForm.setFineAggregate(fineAggregate);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_fine_aggregate")) {
                    Aggregate fineAggregate = labMaterialsForm.getFineAggregate();
                    try {
                        fineAggregate.save();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_fine_aggregate");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_fine_aggregate_as")) {
                    Aggregate fineAggregate = labMaterialsForm.getFineAggregate();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueAggregateName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("fine_aggregate_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    fineAggregate.setName(name);
                    try {
                        fineAggregate.saveAs();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_fine_aggregate");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("new_fine_aggregate")) {
                    Aggregate fineAggregate = new Aggregate();
                    labMaterialsForm.setFineAggregate(fineAggregate);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_fine_aggregate_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_fine_aggregate")) {
                    Aggregate fineAggregate = labMaterialsForm.getFineAggregate();
                    try {
                        fineAggregate.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleting_fine_aggregate");
                        out.flush();
                        return null;
                    }

                    try {
                        fineAggregate = Aggregate.load(CementDatabase.getFirstFineAggregateName());
                        labMaterialsForm.setFineAggregate(fineAggregate);
                    } catch (NoFineAggregateException ex) {
                        return (mapping.findForward("no_fine_aggregate"));
                    }
                    return (mapping.findForward("success"));


                } else if (action.equalsIgnoreCase("new_fly_ash")) {
                    FlyAsh flyAsh = new FlyAsh();
                    labMaterialsForm.setFlyAsh(flyAsh);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("sum_fly_ash_vol_frac")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_fly_ash")) {

                    String name = labMaterialsForm.getFlyAsh().getName();

                    FlyAsh flyAsh;
                    if (name == null || name.equalsIgnoreCase("")) {
                        flyAsh = new FlyAsh();
                    } else {
                        flyAsh = FlyAsh.load(name);
                        labMaterialsForm.setFlyAsh(flyAsh);
                        return (mapping.findForward("success"));
                    }

                } else if (action.equalsIgnoreCase("save_fly_ash")) {
                    FlyAsh flyAsh = labMaterialsForm.getFlyAsh();

                    try {
                        flyAsh.save();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_fly_ash");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));

                } else if (action.equalsIgnoreCase("save_fly_ash_as")) {
                    FlyAsh flyAsh = labMaterialsForm.getFlyAsh();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueFlyAshName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("fly_ash_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    flyAsh.setName(name);
                    try {
                        flyAsh.saveAs();
                    } catch (SQLException ex) {

                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_fly_ash");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_fly_ash")) {
                    FlyAsh flyAsh = labMaterialsForm.getFlyAsh();
                    try {
                        flyAsh.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_fly_ash");
                        out.flush();
                        return null;
                    }
                    
                    try {
                        flyAsh = FlyAsh.load(CementDatabase.getFirstFlyAshName());
                        labMaterialsForm.setFlyAsh(flyAsh);
                    } catch (NoFlyAshException ex) {
                        return (mapping.findForward("no_fly_ash"));
                    }
                    return (mapping.findForward("success"));



                } else if (action.equalsIgnoreCase("update_slag_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_slag")) {

                    String name = labMaterialsForm.getSlag().getName();

                    Slag slag;
                    if (name == null || name.equalsIgnoreCase("")) {
                        slag = new Slag();
                    } else {
                        slag = Slag.load(name);
                        labMaterialsForm.setSlag(slag);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("new_slag")) {
                    Slag slag = new Slag();
                    labMaterialsForm.setSlag(slag);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_slag")) {
                    Slag slag = labMaterialsForm.getSlag();
                    try {
                        slag.save();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_slag");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_slag_as")) {
                    Slag slag = labMaterialsForm.getSlag();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueSlagName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("slag_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    slag.setName(name);
                    try {
                        slag.saveAs();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_slag");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_slag")) {
                    Slag slag = labMaterialsForm.getSlag();
                    try {
                        slag.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_slag");
                        out.flush();
                        return null;
                    }

                    try {
                        slag = Slag.load(CementDatabase.getFirstSlagName());
                        labMaterialsForm.setSlag(slag);
                    } catch (NoSlagException ex) {
                        return (mapping.findForward("no_slag"));
                    }
                    return (mapping.findForward("success"));



                } else if (action.equalsIgnoreCase("new_inert_filler")) {
                    InertFiller inertFiller = new InertFiller();
                    labMaterialsForm.setInertFiller(inertFiller);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_inert_filler")) {

                    String name = labMaterialsForm.getInertFiller().getName();

                    InertFiller inertFiller;
                    if (name == null || name.equalsIgnoreCase("")) {
                        inertFiller = new InertFiller();
                    } else {
                        inertFiller = InertFiller.load(name);
                        labMaterialsForm.setInertFiller(inertFiller);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_inert_filler_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_inert_filler")) {
                    InertFiller inertFiller = labMaterialsForm.getInertFiller();
                    try {

                        inertFiller.save();
                    } catch (SQLException ex) {

                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_inert_filler");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_inert_filler_as")) {
                    InertFiller inertFiller = labMaterialsForm.getInertFiller();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueInertFillerName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("inert_filler_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    inertFiller.setName(name);
                    try {
                        inertFiller.saveAs();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_inert_filler");
                        out.flush();
                        return null;
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_inert_filler")) {
                    InertFiller inertFiller = labMaterialsForm.getInertFiller();
                    try {
                        inertFiller.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_inert_filler");
                        out.flush();
                        return null;
                    }

                    try {
                        inertFiller = InertFiller.load(CementDatabase.getFirstInertFillerName());
                        labMaterialsForm.setInertFiller(inertFiller);
                    } catch (NoInertFillerException ex) {
                        return (mapping.findForward("no_inert_filler"));
                    }
                    return (mapping.findForward("success"));
                    


                } else if (action.equalsIgnoreCase("new_cement_data_file")) {
                    String type = labMaterialsForm.getCementDataFile().getType();
                    DBFile cementDataFile = new DBFile(type);
                    labMaterialsForm.setCementDataFile(cementDataFile);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_cement_data_file")) {

                    String name = labMaterialsForm.getCementDataFile().getName();

                    DBFile cementDataFile;
                    if (name == null || name.equalsIgnoreCase("")) {
                        String type = labMaterialsForm.getCementDataFile().getType();
                        cementDataFile = new DBFile(type);
                    } else {
                        cementDataFile = DBFile.load(name);
                        labMaterialsForm.setCementDataFile(cementDataFile);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_cement_data_file")) {
                    DBFile cementDataFile = labMaterialsForm.getCementDataFile();
                    try {

                        cementDataFile.saveFromStrings();
                    } catch (SQLException ex) {

                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_cement_data_file");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_cement_data_file_as")) {
                    DBFile cementDataFile = labMaterialsForm.getCementDataFile();

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
                    DBFile dbFile = labMaterialsForm.getCementDataFile();
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
                        labMaterialsForm.setCementDataFile(dbFile);
                    } catch (DBFileException ex) {
                        return (mapping.findForward("no_cement_data_file"));
                    }
                    return (mapping.findForward("success"));


                }
            } catch (DBFileException ex) {
                if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                    return (mapping.findForward("no_psd"));
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
        return (mapping.findForward("succes"));
    }
}
