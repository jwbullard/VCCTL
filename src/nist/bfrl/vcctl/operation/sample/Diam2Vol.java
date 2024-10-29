/*
 * Diam2Vol.java
 *
 * Created on April 18, 2005, 11:24 AM
 */

package nist.bfrl.vcctl.operation.sample;


/**
 *
 * @author tahall
 */
public class Diam2Vol {
    
    /** Creates a new instance of Diam2Vol */
    public Diam2Vol() {
    }
    
    /**
     *  Compute integer number of pixels in
     *  a sphere of given diameter (in pixels)
     */
    public static long volume(double diameter) {
        long count = 0;
        int i,j,k;
	int idiam,irad;
	double dist,radius,ftmp;
	double xdist,ydist,zdist;

        idiam = (int)(diameter + 0.5);
	irad = (idiam - 1) / 2;
	radius = 0.5 * diameter;
	
	for (k = -(irad); k <= (irad); k++) {
		ftmp = (double)(k);
		zdist = ftmp * ftmp;
		for (j = -(irad); j <= (irad); j++) {
			ftmp = (double)(j);
			ydist = ftmp * ftmp;
			for (i = -(irad); i <= (irad); i++) {
				ftmp = (double)(i);
				xdist = ftmp * ftmp;
				dist = Math.sqrt(xdist + ydist + zdist);
				if ((dist - 0.5) <= ((double)irad)) count++;
			}
		}
	}

	return(count);

    }
}
