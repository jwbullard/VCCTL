/*
 * HydrateMixAction.java
 *
 * Created on June 14, 2007, 10:59 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.operation.hydration;

import java.sql.SQLException;
import java.util.List;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.NullMicrostructureException;
import nist.bfrl.vcctl.exceptions.NullMicrostructureFormException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 *
 * @author mscialom
 */
public class InitializeHydrationAction extends Action  {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws NullMicrostructureException, NullMicrostructureFormException {
        
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                
                HydrateMixForm hydrateMixForm = (HydrateMixForm)form;
                try {
                    
                    List<String> userMixList = OperationDatabase.finishedRunningOrQueuedOperationsNamesOfTypeForUser(Constants.MICROSTUCTURE_OPERATION_TYPE,userName);
                    
                    if (userMixList != null && userMixList.size() > 0) {
                        hydrateMixForm.setUser_mix_list(userMixList);
                        hydrateMixForm.setMicrostructure(userMixList.get(0));
                        // hydrateMixForm.reset(mapping,request);
                        // hydrateMixForm.updateMicrostructureData(userName);
                    } else {
                        return mapping.findForward("no_mix_for_user");
                    }
                    
                    hydrateMixForm.init(userName);
                } catch (NullMicrostructureFormException ex) {
                    ex.printStackTrace();
                } catch (NullMicrostructureException ex) {
                    ex.printStackTrace();
                } catch (SQLArgumentException ex) {
                    return (mapping.findForward("incorrect_name"));
                } catch (SQLException ex) {
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