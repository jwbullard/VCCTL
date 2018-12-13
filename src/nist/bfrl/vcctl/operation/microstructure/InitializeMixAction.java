/*
 * InitializeMixAction.java
 *
 * Created on June 10, 2005, 2:41 PM
 */

package nist.bfrl.vcctl.operation.microstructure;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.exceptions.*;
import org.apache.struts.action.*;
import java.io.*;
import java.util.concurrent.*;
import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.operation.*;

/**
 *
 * @author tahall
 */
public class InitializeMixAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                GenerateMicrostructureForm microStructure = (GenerateMicrostructureForm)form;
                try {
                    microStructure.reset(userName);
                } catch (NoFlyAshException ex) {
                    return mapping.findForward("no_fly_ash");
                } catch (NoSlagException ex) {
                    return mapping.findForward("no_slag");
                } catch (NoInertFillerException ex) {
                    return mapping.findForward("no_inert_filler");
                } catch (DBFileException ex) {
                    if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                        return (mapping.findForward("no_psd"));
                    }
                } catch (NoCementException ex) {
                    return mapping.findForward("no_cement");
                } catch (NoFineAggregateGradingException ex) {
                    return mapping.findForward("no_fine_aggregate_grading");
                } catch (NoCoarseAggregateException ex) {
                    return mapping.findForward("no_coarse_aggregate");
                } catch (NoCoarseAggregateGradingException ex) {
                    return mapping.findForward("no_coarse_aggregate_grading");
                } catch (NoFineAggregateException ex) {
                    return mapping.findForward("no_fine_aggregate");
                } catch (SQLArgumentException ex) {
                    return (mapping.findForward("incorrect_name"));
                } catch (SQLException ex) {
                    String msg = ex.getMessage();
                    String smsg = ex.getSQLState();
                    return mapping.findForward("database_problem");
                }
                
                return mapping.findForward("success");
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }
}
