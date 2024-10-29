/*
 * ElasticModuliAction.java
 *
 * Created on May 25, 2006, 3:18 PM
 */

package nist.bfrl.vcctl.properties.mechanical;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nist.bfrl.vcctl.util.Constants;

import org.apache.struts.action.Action;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionMapping;
import org.apache.struts.action.ActionForward;

import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.operation.OperationState;

/**
 *
 * @author tahall
 * @version
 */

public class ElasticModuliAction extends Action {
    
    /* forward name="success" path="" */
    private final static String SUCCESS = "success";
    private final static String FAILURE = "failure";
    
    /**
     * This is the action called from the Struts framework.
     * @param mapping The ActionMapping used to select this instance.
     * @param form The optional ActionForm bean for this request.
     * @param request The HTTP Request we are processing.
     * @param response The HTTP Response we are processing.
     * @throws java.lang.Exception
     * @return
     */
    public ActionForward execute(ActionMapping mapping,
            ActionForm  form,
            HttpServletRequest request,
            HttpServletResponse response)
            throws Exception {
        
        ElasticModuliForm emf = (ElasticModuliForm)form;
        
        if (emf.getMicrostructure().length() < 1) {
            return mapping.findForward(FAILURE);
        }
        
        /*
         * Otherwise, queue up an elastic moduli calculation
         */
        String opname = emf.getMicrostructure();
        String elastic_input = emf.getElasticInput();
        opname = opname.replace(".img", ".ela");
        
        User user = (User)request.getSession().getAttribute("user");
        String userName = user.getName();

        ServerFile.writeUserOpTextFile(userName, opname, "elastic.in", elastic_input);
        
        Operation op = new Operation(opname,userName,Constants.ELASTIC_MODULI_OPERATION_TYPE);
        
        byte[] state = OperationState.save_to_Xml(emf);
        op.setState(state);
        OperationDatabase.queueOperation(op);
        
        return mapping.findForward(SUCCESS);
    }
}
