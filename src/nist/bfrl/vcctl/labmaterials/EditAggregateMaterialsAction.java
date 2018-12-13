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
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.NoCoarseAggregateException;
import nist.bfrl.vcctl.exceptions.NoFineAggregateException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import org.apache.struts.action.*;
import org.apache.struts.upload.FormFile;

/**
 *
 * @author bullard
 */
public class EditAggregateMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        AggregateMaterialsForm aggregateMaterialsForm = (AggregateMaterialsForm) form;

        String action = request.getParameter("action");
        String coarseAggDisplayName;
        String coarseAggName;
        String fineAggDisplayName;
        String fineAggName;

        if (action != null) {
            try {
                
                if (action.equalsIgnoreCase("change_coarse_aggregate")) {

                    Aggregate coarseAggregate = aggregateMaterialsForm.getCoarseAggregate();
                    coarseAggDisplayName = coarseAggregate.getDisplay_name();
                    coarseAggName = coarseAggregate.getName();

                    if (coarseAggDisplayName == null || coarseAggDisplayName.equalsIgnoreCase("")) {
                        coarseAggregate = new Aggregate();
                        request.setAttribute("coarseAggName", coarseAggName);
                    } else {
                        coarseAggregate = Aggregate.load(coarseAggDisplayName);
                        coarseAggName = coarseAggregate.getName();
                        aggregateMaterialsForm.setCoarseAggregate(coarseAggregate);
                        request.setAttribute("coarseAggName", coarseAggName);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_coarse_aggregate")) {
                    Aggregate coarseAggregate = aggregateMaterialsForm.getCoarseAggregate();
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
                    Aggregate coarseAggregate = aggregateMaterialsForm.getCoarseAggregate();

                    coarseAggDisplayName = request.getParameter("display_name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueAggregateDisplayName(coarseAggDisplayName)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("coarse_aggregate_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    coarseAggregate.setDisplay_name(coarseAggDisplayName);
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
                    aggregateMaterialsForm.setCoarseAggregate(coarseAggregate);
                    coarseAggName = "new";
                    coarseAggDisplayName = "New Coarse Aggregate";
                    request.setAttribute("coarseAggName", coarseAggName);
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_coarse_aggregate_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_coarse_aggregate")) {
                    Aggregate coarseAggregate = aggregateMaterialsForm.getCoarseAggregate();
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
                        coarseAggName = coarseAggregate.getName();
                        coarseAggDisplayName = coarseAggregate.getDisplay_name();
                        aggregateMaterialsForm.setCoarseAggregate(coarseAggregate);
                        request.setAttribute("coarseAggName", coarseAggName);
                    } catch (NoCoarseAggregateException ex) {
                        return (mapping.findForward("no_coarse_aggregate"));
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("upload_coarse_aggregate")) {

                    FormFile ff = aggregateMaterialsForm.getUploaded_coarse_aggregate_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Aggregate coarse_aggregate = aggregateMaterialsForm.getCoarseAggregate();
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
                        aggregateMaterialsForm.setUploaded_coarse_aggregate_file(null);
                        return mapping.findForward("coarse_aggregate_uploaded");
                    } else {
                        return mapping.findForward("coarse_aggregate_not_uploaded");
                    }

                } else if (action.equalsIgnoreCase("change_fine_aggregate")) {

                    Aggregate fineAggregate = aggregateMaterialsForm.getFineAggregate();
                    fineAggDisplayName = fineAggregate.getDisplay_name();
                    fineAggName = fineAggregate.getName();

                    if (fineAggDisplayName == null || fineAggDisplayName.equalsIgnoreCase("")) {
                        fineAggregate = new Aggregate();
                        request.setAttribute("fineAggName", fineAggName);
                    } else {
                        fineAggregate = Aggregate.load(fineAggDisplayName);
                        fineAggName = fineAggregate.getName();
                        aggregateMaterialsForm.setFineAggregate(fineAggregate);
                        request.setAttribute("fineAggName", fineAggName);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_fine_aggregate")) {
                    Aggregate fineAggregate = aggregateMaterialsForm.getFineAggregate();
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
                    Aggregate fineAggregate = aggregateMaterialsForm.getFineAggregate();

                    fineAggDisplayName = request.getParameter("display_name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueAggregateDisplayName(fineAggDisplayName)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("fine_aggregate_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    fineAggregate.setDisplay_name(fineAggDisplayName);
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
                    aggregateMaterialsForm.setFineAggregate(fineAggregate);
                    fineAggName = "new";
                    fineAggDisplayName = "New Fine Aggregate";
                    request.setAttribute("fineAggName", fineAggName);
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_fine_aggregate_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_fine_aggregate")) {
                    Aggregate fineAggregate = aggregateMaterialsForm.getFineAggregate();
                    try {
                        fineAggregate.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_fine_aggregate");
                        out.flush();
                        return null;
                    }

                    try {
                        fineAggregate = Aggregate.load(CementDatabase.getFirstFineAggregateName());
                        fineAggName = fineAggregate.getName();
                        fineAggDisplayName = fineAggregate.getDisplay_name();
                        aggregateMaterialsForm.setFineAggregate(fineAggregate);
                        request.setAttribute("fineAggName", fineAggName);
                    } catch (NoFineAggregateException ex) {
                        return (mapping.findForward("no_fine_aggregate"));
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("upload_fine_aggregate")) {

                    FormFile ff = aggregateMaterialsForm.getUploaded_fine_aggregate_file();
                    if ((ff.getFileName().length() == 0) ||
                            (ff.getFileName() == null)) {
                        ff.setFileName("Must have a filename");
                        return mapping.findForward("failure");
                    }
                    Aggregate fine_aggregate = aggregateMaterialsForm.getFineAggregate();
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
                    } catch (NullPointerException ex) {
                        System.out.println("Somehow caught a null pointer exception.");
                        ex.printStackTrace();
                    } catch (FileNotFoundException ex) {
                        ex.printStackTrace();
                    } catch (IOException ex) {
                        ex.printStackTrace();
                    }

                    if (fine_aggregate != null) {
                        aggregateMaterialsForm.setUploaded_fine_aggregate_file(null);
                        return mapping.findForward("fine_aggregate_uploaded");
                    } else {
                        return mapping.findForward("fine_aggregate_not_uploaded");
                    }
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
