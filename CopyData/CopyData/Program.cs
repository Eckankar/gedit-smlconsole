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
                if (res.IsCompleted) {
                    data += Convert.ToChar(d.EndInvoke(res));
                } else {
                    System.Console.Write(data);
                    return;    
                }
            }
        }

        delegate int ReadDelegate();
    }
}
