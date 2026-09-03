using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

internal static class AutoApplyDesktop
{
    private static readonly string Root = ResolveProjectRoot();
    private static readonly string Profile = Environment.GetEnvironmentVariable("AUTOAPPLY_CHROME_PROFILE")
        ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "AutoApply", "ChromeProfile");
    private static readonly string OllamaExecutable = ResolveExecutable("AUTOAPPLY_OLLAMA_EXE", "ollama.exe");
    private static readonly string OllamaRoot = Path.GetDirectoryName(OllamaExecutable) ?? Environment.CurrentDirectory;
    private static readonly string OllamaModels = Environment.GetEnvironmentVariable("OLLAMA_MODELS")
        ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".ollama", "models");
    private static readonly string RedisExecutable = ResolveExecutable("AUTOAPPLY_REDIS_EXE", "redis-server.exe");
    private static readonly string RedisRoot = Path.GetDirectoryName(RedisExecutable) ?? Environment.CurrentDirectory;
    private static readonly string RedisData = Path.Combine(Root, "data", "redis");
    private static readonly string LogPath = Path.Combine(Root, "logs", "sucessos", "launcher.log");
    private static readonly string ErrorLogPath = Path.Combine(Root, "logs", "erros", "launcher-errors.log");
    private static readonly List<Process> Children = new List<Process>();
    private static Mutex _mutex;
    private static Form _splash;
    private static Label _splashStatus;
    private static IntPtr _job = IntPtr.Zero;
    private static volatile bool _shuttingDown;

    [STAThread]
    private static void Main()
    {
        bool owns;
        _mutex = new Mutex(true, @"Local\AutoApplyDesktopV2", out owns);
        if (!owns) { MessageBox.Show("O AutoApply já está aberto.", "AutoApply"); return; }
        try
        {
            InitializeJob();
            Application.EnableVisualStyles();
            ShowSplash();
            Log("Iniciando AutoApply");
            SetSplash("Preparando serviços locais...");
            SetSplash("Iniciando Redis...");
            StartServices();
            SetSplash("Abrindo o Google Chrome...");
            var urls = "\"http://127.0.0.1:8000/\"";
            var app = StartChrome("--remote-debugging-port=9222 --remote-allow-origins=http://127.0.0.1:9222 --new-window " + urls + " --start-maximized --no-first-run --disable-background-mode");
            Log("Chrome iniciado PID=" + app.Id);
            CloseSplash();
            app.WaitForExit();
        }
        catch (Exception ex)
        {
            Log("ERRO: " + ex.ToString());
            LogError(ex);
            CloseSplash();
            MessageBox.Show("Não foi possível iniciar o AutoApply.\n\n" + ex.Message, "AutoApply", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            _shuttingDown = true;
            StopChildren();
            if (_job != IntPtr.Zero) { CloseHandle(_job); _job = IntPtr.Zero; }
            if (_mutex != null) _mutex.ReleaseMutex();
        }
    }

    private static void StartServices()
    {
        if (!Directory.Exists(Path.Combine(Root, "backend"))) throw new DirectoryNotFoundException("AutoApply project not found at " + Root + ". Set AUTOAPPLY_ROOT to the cloned repository path.");
        if (!File.Exists(OllamaExecutable)) throw new FileNotFoundException("Ollama was not found. Install it or configure AUTOAPPLY_OLLAMA_EXE.", OllamaExecutable);
        if (!File.Exists(RedisExecutable)) throw new FileNotFoundException("Redis was not found. Install it or configure AUTOAPPLY_REDIS_EXE.", RedisExecutable);
        var pythonExecutable = Path.Combine(Root, ".venv", "Scripts", "python.exe");
        if (!File.Exists(pythonExecutable)) throw new FileNotFoundException("Python virtual environment not found. Follow the installation steps in README.md.", pythonExecutable);
        Directory.CreateDirectory(OllamaModels);
        SetSplash("Iniciando Llama 2 local...");
        Children.Add(Start(OllamaExecutable, "serve", OllamaRoot));
        if (!WaitForPort(11434, 30)) throw new Exception("Ollama não iniciou.");
        Log("Ollama pronto com modelo llama2:7b-chat-q2_K");
        SetSplash("Iniciando Redis...");
        Directory.CreateDirectory(RedisData);
        Children.Add(Start(RedisExecutable, "--bind 127.0.0.1 --port 6379 --dir \"" + RedisData + "\" --appendonly yes", RedisRoot));
        if (!WaitForPort(6379, 15)) throw new Exception("Redis não iniciou.");
        Log("Redis pronto");
        SetSplash("Iniciando backend e banco local...");
        Children.Add(Start(pythonExecutable, "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000", Root));
        if (!WaitForPort(8000, 45)) throw new Exception("A API local não iniciou a tempo. Consulte " + LogPath);
        Log("Backend pronto");
    }

    private static Process StartChrome(string arguments)
    {
        Directory.CreateDirectory(Profile);
        var process = Process.Start(new ProcessStartInfo {
            FileName = FindChrome(), Arguments = "--user-data-dir=\"" + Profile + "\" " + arguments,
            UseShellExecute = false
        });
        if (process == null) throw new Exception("Google Chrome não iniciou.");
        AssignToJob(process);
        return process;
    }

    private static Process Start(string file, string arguments, string workingDirectory)
    {
        var info = new ProcessStartInfo { FileName=file, Arguments=arguments, WorkingDirectory=workingDirectory, UseShellExecute=false, CreateNoWindow=true, WindowStyle=ProcessWindowStyle.Hidden, RedirectStandardOutput=true, RedirectStandardError=true };
        info.EnvironmentVariables["PYTHONUTF8"] = "1";
        info.EnvironmentVariables["OLLAMA_MODELS"] = OllamaModels;
        info.EnvironmentVariables["OLLAMA_CONTEXT_LENGTH"] = "2048";
        info.EnvironmentVariables["OLLAMA_FLASH_ATTENTION"] = "1";
        info.EnvironmentVariables["OLLAMA_KV_CACHE_TYPE"] = "q4_0";
        info.EnvironmentVariables["OLLAMA_MAX_LOADED_MODELS"] = "1";
        info.EnvironmentVariables["OLLAMA_NUM_PARALLEL"] = "1";
        var stderr = new StringBuilder();
        var process = new Process { StartInfo=info, EnableRaisingEvents=true };
        process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) Log(Path.GetFileName(file) + ": " + e.Data); };
        process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) { lock(stderr) { stderr.AppendLine(e.Data); } Log(Path.GetFileName(file) + " [stderr]: " + e.Data); } };
        process.Exited += delegate(object sender, EventArgs e) { try { if(!_shuttingDown && process.ExitCode!=0) { string captured; lock(stderr) { captured=stderr.ToString(); } LogProcessError(file, process.ExitCode, captured); } } catch {} };
        process.Start();
        AssignToJob(process);
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
        Log("Processo iniciado: " + file + " " + arguments);
        return process;
    }

    private static string FindChrome()
    {
        var candidates = new[] {
            Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            Environment.ExpandEnvironmentVariables(@"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            Environment.ExpandEnvironmentVariables(@"%LocalAppData%\Google\Chrome\Application\chrome.exe")
        };
        foreach (var path in candidates) if (File.Exists(path)) return path;
        throw new FileNotFoundException("Google Chrome não encontrado.");
    }

    private static string ResolveProjectRoot()
    {
        var configured = Environment.GetEnvironmentVariable("AUTOAPPLY_ROOT");
        var candidates = new[] { configured, AppDomain.CurrentDomain.BaseDirectory, Environment.CurrentDirectory };
        foreach (var candidate in candidates) {
            if (String.IsNullOrWhiteSpace(candidate)) continue;
            var fullPath = Path.GetFullPath(candidate);
            if (Directory.Exists(Path.Combine(fullPath, "backend")) && File.Exists(Path.Combine(fullPath, "requirements.txt"))) return fullPath;
        }
        return Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
    }

    private static string ResolveExecutable(string environmentVariable, string executableName)
    {
        var configured = Environment.GetEnvironmentVariable(environmentVariable);
        if (!String.IsNullOrWhiteSpace(configured) && File.Exists(configured)) return Path.GetFullPath(configured);
        foreach (var directory in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator)) {
            var candidate = Path.Combine(directory.Trim(), executableName);
            if (File.Exists(candidate)) return candidate;
        }
        return String.IsNullOrWhiteSpace(configured) ? executableName : Path.GetFullPath(configured);
    }

    private static bool WaitForPort(int port, int seconds)
    {
        for (var i=0;i<seconds*4;i++) {
            try {
                using(var client=new TcpClient()) {
                    var task=client.ConnectAsync("127.0.0.1",port);
                    if(task.Wait(200) && !task.IsFaulted && !task.IsCanceled && client.Connected) return true;
                }
            } catch {}
            Application.DoEvents();
            Thread.Sleep(250);
        }
        return false;
    }

    private static void ShowSplash()
    {
        _splash = new Form { Text="AutoApply", Width=440, Height=160, StartPosition=FormStartPosition.CenterScreen, FormBorderStyle=FormBorderStyle.FixedDialog, MaximizeBox=false, MinimizeBox=false, TopMost=true, BackColor=System.Drawing.Color.FromArgb(16,21,29) };
        var title = new Label { Text="AutoApply", Left=28, Top=25, Width=360, Height=28, ForeColor=System.Drawing.Color.FromArgb(121,224,179), Font=new System.Drawing.Font("Segoe UI",14,System.Drawing.FontStyle.Bold) };
        _splashStatus = new Label { Text="Preparando aplicativo...", Left=29, Top=67, Width=370, Height=25, ForeColor=System.Drawing.Color.FromArgb(185,196,209), Font=new System.Drawing.Font("Segoe UI",9) };
        _splash.Controls.Add(title);
        _splash.Controls.Add(_splashStatus);
        _splash.Show();
        Application.DoEvents();
    }

    private static void SetSplash(string status) { if(_splashStatus!=null) { _splashStatus.Text=status; Application.DoEvents(); } }
    private static void CloseSplash() { try { if(_splash!=null) { _splash.Close(); _splash.Dispose(); _splash=null; } } catch {} }

    private static void Log(string message)
    {
        try {
            Directory.CreateDirectory(Path.GetDirectoryName(LogPath));
            lock(Children) { File.AppendAllText(LogPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " " + message + Environment.NewLine); }
        } catch {}
    }

    private static void LogError(Exception error)
    {
        try {
            Directory.CreateDirectory(Path.GetDirectoryName(ErrorLogPath));
            File.AppendAllText(ErrorLogPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " LAUNCHER ERROR" + Environment.NewLine + error.ToString() + Environment.NewLine + Environment.NewLine);
        } catch {}
    }

    private static void LogProcessError(string file, int exitCode, string stderr)
    {
        try {
            Directory.CreateDirectory(Path.GetDirectoryName(ErrorLogPath));
            File.AppendAllText(ErrorLogPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff") + " PROCESS ERROR: " + file + " exit=" + exitCode + Environment.NewLine + stderr + Environment.NewLine);
        } catch {}
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JobBasicLimitInformation
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public IntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JobExtendedLimitInformation
    {
        public JobBasicLimitInformation BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)]
    private static extern IntPtr CreateJobObject(IntPtr securityAttributes, string name);

    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr information, uint informationLength);

    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool CloseHandle(IntPtr handle);

    private static void InitializeJob()
    {
        _job = CreateJobObject(IntPtr.Zero, null);
        if (_job == IntPtr.Zero) throw new Exception("Não foi possível criar o controle de processos do AutoApply. Win32=" + Marshal.GetLastWin32Error());
        var info = new JobExtendedLimitInformation();
        info.BasicLimitInformation.LimitFlags = 0x00002000;
        var length = Marshal.SizeOf(typeof(JobExtendedLimitInformation));
        var pointer = Marshal.AllocHGlobal(length);
        try {
            Marshal.StructureToPtr(info, pointer, false);
            if (!SetInformationJobObject(_job, 9, pointer, (uint)length)) throw new Exception("Não foi possível configurar o encerramento automático. Win32=" + Marshal.GetLastWin32Error());
        } finally { Marshal.FreeHGlobal(pointer); }
    }

    private static void AssignToJob(Process process)
    {
        if (_job == IntPtr.Zero || !AssignProcessToJobObject(_job, process.Handle)) {
            try { process.Kill(); } catch {}
            throw new Exception("Não foi possível vincular " + process.ProcessName + " ao encerramento automático. Win32=" + Marshal.GetLastWin32Error());
        }
    }

    private static void StopOrphans()
    {
        using(var searcher=new ManagementObjectSearcher("SELECT ProcessId, CommandLine FROM Win32_Process"))
        foreach(ManagementObject item in searcher.Get()) {
            var command=Convert.ToString(item["CommandLine"]); if(String.IsNullOrEmpty(command)) continue;
            if(command.IndexOf(Root,StringComparison.OrdinalIgnoreCase)>=0 || command.IndexOf(RedisExecutable,StringComparison.OrdinalIgnoreCase)>=0) {
                var pid=Convert.ToInt32((UInt32)item["ProcessId"]); if(pid!=Process.GetCurrentProcess().Id) KillTree(pid);
            }
        }
        Thread.Sleep(600);
    }

    private static void StopProfileChrome()
    {
        using(var searcher=new ManagementObjectSearcher("SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='chrome.exe'"))
        foreach(ManagementObject item in searcher.Get()) {
            var command=Convert.ToString(item["CommandLine"]); if(!String.IsNullOrEmpty(command) && command.IndexOf(Profile,StringComparison.OrdinalIgnoreCase)>=0) KillTree(Convert.ToInt32((UInt32)item["ProcessId"]));
        }
    }

    private static void StopChildren() { for(var i=Children.Count-1;i>=0;i--) try { if(!Children[i].HasExited) KillTree(Children[i].Id); } catch {} }
    private static void KillTree(int pid) { try { using(var killer=Process.Start(new ProcessStartInfo { FileName="taskkill.exe", Arguments="/PID "+pid+" /T /F", UseShellExecute=false, CreateNoWindow=true })) { if(killer!=null) killer.WaitForExit(5000); } } catch {} }
}
