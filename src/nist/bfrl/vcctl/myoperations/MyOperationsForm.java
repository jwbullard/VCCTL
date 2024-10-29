/*
 * MyOperationsForm.java
 *
 * Created on September 11, 2007, 4:47 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myoperations;

import java.util.List;
import nist.bfrl.vcctl.database.Operation;
import org.apache.struts.action.ActionForm;

/**
 *
 * @author mscialom
 */
public class MyOperationsForm extends ActionForm {
    
    /**
     * Holds value of property runningOperations.
     */
    private List<Operation> runningOperations;
    
    /**
     * Indexed getter for property runningOperations.
     * @param index Index of the property.
     * @return Value of the property at <CODE>index</CODE>.
     */
    public Operation getRunningOperation(int index) {
        return this.runningOperations.get(index);
    }
    
    /**
     * Getter for property runningOperations.
     * @return Value of property runningOperations.
     */
    public List<Operation> getRunningOperations() {
        return this.runningOperations;
    }
    
    public void setRunningOperations(List<Operation> runningOperations) {
        this.runningOperations = runningOperations;
    }
    
    /**
     * Holds value of property finishedOperations.
     */
    private List<Operation> finishedOperations;
    
    /**
     * Indexed getter for property finishedOperations.
     * @param index Index of the property.
     * @return Value of the property at <CODE>index</CODE>.
     */
    public Operation getFinishedOperation(int index) {
        return this.finishedOperations.get(index);
    }
    
    /**
     * Getter for property finishedOperations.
     * @return Value of property finishedOperations.
     */
    public List<Operation> getFinishedOperations() {
        return this.finishedOperations;
    }
    
    public void setFinishedOperations(List<Operation> finishedOperations) {
        this.finishedOperations = finishedOperations;
    }
    
    /**
     * Holds value of property cancelledOperations.
     */
    private List<Operation> cancelledOperations;
    
    /**
     * Indexed getter for property cancelledOperations.
     * @param index Index of the property.
     * @return Value of the property at <CODE>index</CODE>.
     */
    public Operation getCancelledOperation(int index) {
        return this.cancelledOperations.get(index);
    }
    
    /**
     * Getter for property cancelledOperations.
     * @return Value of property cancelledOperations.
     */
    public List<Operation> getCancelledOperations() {
        return this.cancelledOperations;
    }
    
    public void setCancelledOperations(List<Operation> cancelledOperations) {
        this.cancelledOperations = cancelledOperations;
    }
    
    /**
     * Holds value of property queuedOperations.
     */
    private List<Operation> queuedOperations;
    
    /**
     * Indexed getter for property queuedOperations.
     * @param index Index of the property.
     * @return Value of the property at <CODE>index</CODE>.
     */
    public Operation getQueuedOperation(int index) {
        return this.queuedOperations.get(index);
    }
    
    /**
     * Getter for property queuedOperations.
     * @return Value of property queuedOperations.
     */
    public List<Operation> getQueuedOperations() {
        return this.queuedOperations;
    }
    
    public void setQueuedOperations(List<Operation> queuedOperations) {
        this.queuedOperations = queuedOperations;
    }

    /**
     * Holds value of property operationToCancel.
     */
    private String operationToCancel;

    /**
     * Getter for property selectedRunningOperationName.
     * @return Value of property selectedRunningOperationName.
     */
    public String getOperationToCancel() {
        return this.operationToCancel;
    }

    /**
     * Setter for property selectedRunningOperationName.
     * @param selectedRunningOperationName New value of property selectedRunningOperationName.
     */
    public void setOperationToCancel(String operationToCancel) {
        this.operationToCancel = operationToCancel;
    }

    /**
     * Holds value of property operationToDelete.
     */
    private String operationToDelete;

    /**
     * Getter for property selectedFinishedOperationName.
     * @return Value of property selectedFinishedOperationName.
     */
    public String getOperationToDelete() {
        return this.operationToDelete;
    }

    /**
     * Setter for property selectedFinishedOperationName.
     * @param selectedFinishedOperationName New value of property selectedFinishedOperationName.
     */
    public void setOperationToDelete(String operationToDelete) {
        this.operationToDelete = operationToDelete;
    }

    /**
     * Holds value of property operationToView.
     */
    private String operationToView;

    /**
     * Getter for property operationToView.
     * @return Value of property operationToView.
     */
    public String getOperationToView() {
        return this.operationToView;
    }

    /**
     * Setter for property operationToView.
     * @param operationToView New value of property operationToView.
     */
    public void setOperationToView(String operationToView) {
        this.operationToView = operationToView;
    }
}
