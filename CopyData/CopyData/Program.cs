using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace CopyData {
    class Program {
        static void Main(string[] args) {
            String data = "";
            while (true) {
                ReadDelegate d = System.Console.Read;
                IAsyncResult res = d.BeginInvoke(null, null);
                res.AsyncWaitHandle.WaitOne(10); // 10 ms blocking wait
                if (!res.IsCompleted) break;
                
                int result = d.EndInvoke(res);
                if (result == -1) break; // End of stream
                data += Convert.ToChar(result);
            }
            System.Console.Write(data);
            return;    
        }

        delegate int ReadDelegate();
    }
}
