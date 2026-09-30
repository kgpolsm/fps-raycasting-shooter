$root = $PSScriptRoot
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, 8081)
$listener.Start()
Write-Host 'Game server: http://localhost:8081/'
while ($true) {
    $client = $listener.AcceptTcpClient()
    try {
        $stream = $client.GetStream()
        $reader = [System.IO.StreamReader]::new($stream)
        $requestLine = $reader.ReadLine()
        while (($line = $reader.ReadLine()) -ne '') { }
        $requestPath = '/fps_game.html'
        if ($requestLine -match '^GET\s+([^\s?]+)') { $requestPath = $matches[1] }
        if ($requestPath -eq '/') { $requestPath = '/fps_game.html' }
        $filePath = Join-Path $root $requestPath.TrimStart('/')
        if (Test-Path -LiteralPath $filePath) {
            $body = [System.IO.File]::ReadAllBytes($filePath)
            $header = "HTTP/1.1 200 OK`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($body.Length)`r`nConnection: close`r`n`r`n"
        } else {
            $body = [System.Text.Encoding]::UTF8.GetBytes('Not found')
            $header = "HTTP/1.1 404 Not Found`r`nContent-Type: text/plain; charset=utf-8`r`nContent-Length: $($body.Length)`r`nConnection: close`r`n`r`n"
        }
        $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($header)
        $stream.Write($headerBytes, 0, $headerBytes.Length)
        $stream.Write($body, 0, $body.Length)
        $stream.Flush()
    } finally {
        $client.Close()
    }
}
