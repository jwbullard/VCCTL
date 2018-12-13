/*
 * InitializeOperationsAction.java
 *
 * Created on September 11, 2007, 4:51 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myoperations;

import java.sql.SQLException;
import java.util.List;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.Operation;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

/**
 *
 * @author mscialom
 */
public class InitializeOperationsAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        MyOperationsForm myOperationsForm = (MyOperationsForm)form;
        
        HttpSession session = request.getSession();
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                List<Operation> runningOperations;
                try {
                    runningOperations = OperationDatabase.getOperationsByStatusForUserChangeSeparator(Constants.OPERATION_RUNNING_STATUS, "start", userName);
                    myOperationsForm.setRunningOperations(runningOperations);
                    List<Operation> finishedOperations = OperationDatabase.getOperationsByStatusForUserChangeSeparator(Constants.OPERATION_FINISHED_STATUS,"start",userName);
                    myOperationsForm.setFinishedOperations(finishedOperations);
                    List<Operation> queuedOperations = OperationDatabase.getOperationsByStatusForUserChangeSeparator(Constants.OPERATION_QUEUED_STATUS,"start",userName);
                    myOperationsForm.setQueuedOperations(queuedOperations);
                    List<Operation> cancelledOperations = OperationDatabase.getOperationsByStatusForUserChangeSeparator(Constants.OPERATION_CANCELLED_STATUS,"start",userName);
                    myOperationsForm.setCancelledOperations(cancelledOperations);
                    if (runningOperations.size() <= 0 && finishedOperations.size() <= 0 && queuedOperations.size() <= 0 && cancelledOperations.size() <= 0) {
                        return (mapping.findForward("no_operation_for_user"));
                    }
                } catch (SQLException ex) {
                    return mapping.findForward("database_problem");
                } catch (SQLArgumentException ex) {
                    ex.printStackTrace();
                }
                return (mapping.findForward("success"));
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }
    
}
