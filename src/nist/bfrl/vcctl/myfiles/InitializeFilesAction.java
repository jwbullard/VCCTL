/*
 * InitializeFilesAction.java
 *
 * Created on September 13, 2007, 4:28 AM
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
public class InitializeFilesAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        MyFilesForm myFilesForm = (MyFilesForm)form;
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                Map<String, Operation> microstructureOperations;
                try {
                    microstructureOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.MICROSTUCTURE_OPERATION_TYPE, "start", userName);
                    myFilesForm.setMicrostructureOperations(microstructureOperations);
                    Map<String,Operation> hydrationOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.HYDRATION_OPERATION_TYPE,"start",userName);
                    myFilesForm.setHydrationOperations(hydrationOperations);
                    Map<String,Operation> aggregateOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.AGGREGATE_OPERATION_TYPE,"start",userName);
                    myFilesForm.setAggregateOperations(aggregateOperations);
                    Map<String,Operation> elasticModuliOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.ELASTIC_MODULI_OPERATION_TYPE,"start",userName);
                    myFilesForm.setElasticModuliOperations(elasticModuliOperations);
                    Map<String,Operation> transportFactorOperations = OperationDatabase.getOperationsOfTypeForUserChangeSeparator(Constants.TRANSPORT_FACTOR_OPERATION_TYPE,"start",userName);
                    myFilesForm.setTransportFactorOperations(transportFactorOperations);
                    if (microstructureOperations.size() <= 0 && hydrationOperations.size() <= 0 && aggregateOperations.size() <= 0 && elasticModuliOperations.size() <= 0 && transportFactorOperations.size() <= 0) {
                        return (mapping.findForward("no_file_for_user"));
                    }
                } catch (SQLException ex) {
                    return mapping.findForward("database_problem");
                } catch (SQLArgumentException ex) {
                    ex.printStackTrace();
                }
                String operationToView = (String)request.getAttribute("view_operation");
                if (operationToView != null && operationToView.length() > 0) {
                    boolean found = false;
                    Map<String,Operation> operationsList = myFilesForm.getMicrostructureOperations();
                    Operation operation = operationsList.get(operationToView);
                    
                    if (operation != null) {
                        operation.setViewOperation(true);
                        return (mapping.findForward("success"));
                    }
                    
                    operationsList = myFilesForm.getHydrationOperations();
                    operation = operationsList.get(operationToView);
                    
                    if (operation != null) {
                        operation.setViewOperation(true);
                        return (mapping.findForward("success"));
                    }
                    
                    operationsList = myFilesForm.getAggregateOperations();
                    operation = operationsList.get(operationToView);
                    
                    if (operation != null) {
                        operation.setViewOperation(true);
                        return (mapping.findForward("success"));
                    }
                    
                    operationsList = myFilesForm.getElasticModuliOperations();
                    operation = operationsList.get(operationToView);
                    
                    if (operation != null) {
                        operation.setViewOperation(true);
                        return (mapping.findForward("success"));
                    }

                    operationsList = myFilesForm.getTransportFactorOperations();
                    operation = operationsList.get(operationToView);

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
