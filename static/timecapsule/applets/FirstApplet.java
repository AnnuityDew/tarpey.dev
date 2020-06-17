/*Michael Tarpey
 *Block 1A
 *5-18-09*/
 
 import java.applet.Applet;
 import java.awt.*;
 
 public class FirstApplet extends Applet
 {
 	public void paint(Graphics oops)
 	{
 		oops.drawLine(150, 50, 150, 450);
 		oops.drawLine(150, 450, 450, 150);
 		oops.drawLine(450, 150, 50, 150);
 		oops.drawLine(50, 150, 350, 450);
 		oops.drawLine(350, 450, 350, 50);
 		oops.drawLine(350, 50, 50, 350);
 		oops.drawLine(50, 350, 450, 350);
 		oops.drawLine(450, 350, 150, 50);
 		
 		oops.drawOval(25, 25, 450, 450);
 		
 		
 	}
 }