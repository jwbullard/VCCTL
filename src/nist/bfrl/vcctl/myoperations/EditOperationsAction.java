/*
 * EditOperationsAction.java
 *
 * Created on September 11, 2007, 5:46 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.myoperations;

import java.sql.SQLException;
import java.util.List;
import java.util.Map;
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
public class EditOperationsAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        MyOperationsForm myOperationsForm = (MyOperationsForm) form;

        Map pm = request.getParameterMap();
        HttpSession session = request.getSession();

        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                try {
                    if (pm.containsKey("action")) {
                        String[] actions = (String[]) pm.get("action");
                        String action = actions[0];

                        if (action.equalsIgnoreCase("cancel_operation")) {
                            String operationName = myOperationsForm.getOperationToCancel();
                            OperationDatabase.cancelOperationForUser(operationName, userName);
                        } else if (action.equalsIgnoreCase("delete_operation")) {
                            String operationName = myOperationsForm.getOperationToDelete();
                            OperationDatabase.deleteOperationForUser(operationName, userName);
                        } else if (action.equalsIgnoreCase("view_operation")) {
                            String forwardMessage1 = "";
                            String forwardMessage2 = "";
                            String opName = myOperationsForm.getOperationToView();
                            Operation op = OperationDatabase.getOperationForUser(opName,userName);
                            String toViewType = op.getType();
                            if (toViewType.equalsIgnoreCase(Constants.MICROSTUCTURE_OPERATION_TYPE)) {
                                forwardMessage1 = "view_microstructure_operation";
                                forwardMessage2 = "view_microstructure_operation_files";
                            } else if (toViewType.equalsIgnoreCase(Constants.AGGREGATE_OPERATION_TYPE)) {
                                forwardMessage1 = "view_aggregate_operation";
                                forwardMessage2 = "view_aggregate_operation_files";
                            } else if (toViewType.equalsIgnoreCase(Constants.HYDRATION_OPERATION_TYPE)) {
                                forwardMessage1 = "view_hydration_operation";
                                forwardMessage2 = "view_hydration_operation_files";
                            } else if (toViewType.equalsIgnoreCase(Constants.ELASTIC_MODULI_OPERATION_TYPE)) {
                                forwardMessage1 = "view_mechanical_operation";
                                forwardMessage2 = "view_mechanical_operation_files";
                            } else {
                                forwardMessage1 = "view_transport_operation";
                                forwardMessage2 = "view_transport_operation_files";
                            }
                            request.setAttribute(forwardMessage1, opName);
                            return (mapping.findForward(forwardMessage2));
                        }
                        List<Operation> runningOperations;
                        runningOperations = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_RUNNING_STATUS, "start", userName);
                        myOperationsForm.setRunningOperations(runningOperations);
                        List<Operation> finishedOperations = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_FINISHED_STATUS, "start", userName);
                        myOperationsForm.setFinishedOperations(finishedOperations);
                        List<Operation> queuedOperations = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_QUEUED_STATUS, "start", userName);
                        myOperationsForm.setQueuedOperations(queuedOperations);
                        List<Operation> cancelledOperations = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_CANCELLED_STATUS, "start", userName);
                        myOperationsForm.setCancelledOperations(cancelledOperations);
                        if (runningOperations.size() <= 0 && finishedOperations.size() <= 0 && queuedOperations.size() <= 0 && cancelledOperations.size() <= 0) {
                            return (mapping.findForward("no_operation_for_user"));
                        }
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
