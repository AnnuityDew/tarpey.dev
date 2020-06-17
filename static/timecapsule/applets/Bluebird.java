/*Michael Tarpey
 *Block 1A
 *5-18-09*/
 
 import java.applet.Applet;
 import java.awt.Color;
 import java.awt.*;
 
 public class Bluebird extends Applet
 {
 	public void paint(Graphics wings)
 	{
 		setBackground(Color.cyan);
 		
 		wings.setColor(new Color(165, 102, 71));
 		wings.fillRect(0, 300, 550, 50);
 		
 		wings.setColor(new Color(225, 225, 60));
 		wings.fillRect(225, 300, 25, 50);
 		wings.fillRect(300, 300, 25, 50);
 		
 		wings.setColor(Color.blue);
 		wings.fillRect(200, 100, 150, 200);
 		
 		int[] leftWingX = {200, 200, 100};
 		int[] leftWingY = {150, 250, 200};
 		wings.fillPolygon(leftWingX, leftWingY, 3);
 		
 		int[] rightWingX = {350, 350, 450};
 		int[] rightWingY = {150, 250, 200};
 		wings.fillPolygon(rightWingX, rightWingY, 3);
 		
 		wings.setColor(Color.white);
 		wings.fillOval(225, 125, 40, 40);
 		wings.fillOval(285, 125, 40, 40);
 		 		
 		int[] leftShadeX = {180, 180, 130};
 		int[] leftShadeY = {175, 225, 200};
 		wings.fillPolygon(leftShadeX, leftShadeY, 3);
 		
 		int[] rightShadeX = {370, 370, 420};
 		int[] rightShadeY = {175, 225, 200};
 		wings.fillPolygon(rightShadeX, rightShadeY, 3);
 		
 		wings.setColor(new Color(200, 135, 67));			
 		wings.fillRect(210, 235, 130, 20);
 		wings.setColor(Color.white);			
 		wings.fillRect(210, 255, 130, 35);
 		 		
 		wings.setColor(Color.black);
 		wings.fillOval(235, 135, 20, 20);
 		wings.fillOval(295, 135, 20, 20);
 		
 		wings.setColor(Color.yellow);
 		int[] triangleX = {250, 300, 275};
 		int[] triangleY = {175, 175, 225};
  		wings.fillPolygon(triangleX, triangleY, 3);
  		
  		wings.fillOval(500, -50, 100, 100);
  		
 	}
 }