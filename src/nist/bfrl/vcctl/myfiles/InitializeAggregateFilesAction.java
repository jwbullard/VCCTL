/*
 * InitializeAggregateFilesAction.java
 *
 * Created on October 28, 2011, 3:00 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myfiles;

import java.sql.SQLException;
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
public class InitializeAggregateFilesAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        MyAggregateFilesForm myFilesForm = (MyAggregateFilesForm)form;

        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                Map<String, Operation> aggregateOperations;
                try {
                    aggregateOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.AGGREGATE_OPERATION_TYPE,"start",userName);
                    myFilesForm.setAggregateOperations(aggregateOperations);
                    if (aggregateOperations.size() <= 0) {
                        return (mapping.findForward("no_file_for_user"));
                    }
                } catch (SQLException ex) {
                    return mapping.findForward("database_problem");
                } catch (SQLArgumentException ex) {
                    ex.printStackTrace();
                }
                String operationToView = (String)request.getAttribute("view_aggregate_operation");
                if (operationToView != null && operationToView.length() > 0) {
                    boolean found = false;
                    Map<String,Operation> operationsList = myFilesForm.getAggregateOperations();
                    Operation operation = operationsList.get(operationToView);

                    if (operation != null) {
                        operation.setViewOperation(true);
                        return (mapping.findForward("success"));
                    }

                    return (mapping.findForward("no_such_operation"));
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
