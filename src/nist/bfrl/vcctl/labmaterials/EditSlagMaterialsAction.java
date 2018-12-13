/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoSlagException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

/**
 *
 * @author bullard
 */
public class EditSlagMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        SlagMaterialsForm slagMaterialsForm = (SlagMaterialsForm) form;

        String action = request.getParameter("action");

        if (action != null) {
            try {
                if (action.equalsIgnoreCase("update_slag_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_slag")) {

                    String name = slagMaterialsForm.getSlag().getName();

                    Slag slag;
                    if (name == null || name.equalsIgnoreCase("")) {
                        slag = new Slag();
                    } else {
                        slag = Slag.load(name);
                        slagMaterialsForm.setSlag(slag);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("new_slag")) {
                    Slag slag = new Slag();
                    slagMaterialsForm.setSlag(slag);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_slag")) {
                    Slag slag = slagMaterialsForm.getSlag();
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
                    Slag slag = slagMaterialsForm.getSlag();

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
                    Slag slag = slagMaterialsForm.getSlag();
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
                        slagMaterialsForm.setSlag(slag);
                    } catch (NoSlagException ex) {
                        return (mapping.findForward("no_slag"));
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
        return (mapping.findForward("success"));
    }
}
