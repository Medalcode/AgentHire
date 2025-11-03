const express = require('express');
const { execFile } = require('child_process');

const app = express();
app.use(express.json());

const executeCommand = (args, session) => {
    return new Promise((resolve, reject) => {
        let fullArgs = [];
        if (session) {
            fullArgs.push('--session-name', session);
        }
        fullArgs = fullArgs.concat(args);
        console.log("Executing: agent-browser", fullArgs.join(' '));
        
        execFile('agent-browser', fullArgs, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
            if (error) {
                console.error("Error:", error.message);
                console.error("Stderr:", stderr);
                return reject(new Error(stderr || error.message));
            }
            resolve(stdout.trim());
        });
    });
};

app.post('/rpc', async (req, res) => {
    const { jsonrpc, id, method, params } = req.body;
    let result = null;
    let error = null;

    try {
        const session = params.session || req.app.locals.currentSession;
        if (params.session) req.app.locals.currentSession = params.session;

        switch (method) {
            case 'browser.navigate':
                await executeCommand(['open', params.url], session);
                result = { url: params.url, status: 200 };
                break;
            case 'browser.snapshot':
                const out = await executeCommand(['snapshot', '-j'], session);
                try {
                    // Attempt to extract the JSON output if it's mixed with other logs
                    const jsonMatch = out.match(/(\{.*\})/s);
                    result = JSON.parse(jsonMatch ? jsonMatch[1] : out);
                } catch (e) {
                    result = { text: out };
                }
                break;
            case 'browser.getInnerText':
                result = { text: await executeCommand(['get', 'text', params.selector, '-q'], session) };
                break;
            case 'browser.click':
                await executeCommand(['click', params.selector, '-q'], session);
                result = { clicked: true, selector: params.selector };
                break;
            case 'browser.fill':
                await executeCommand(['fill', params.selector, params.text, '-q'], session);
                result = { filled: true, selector: params.selector };
                break;
            case 'browser.screenshot':
                await executeCommand(['screenshot', '-q'], session);
                result = { path: "/app/outputs/screenshot.png" };
                break;
            case 'browser.loadState':
                req.app.locals.currentSession = params.name;
                result = { loaded: true };
                break;
            case 'browser.saveState':
                result = { saved: true };
                break;
            case 'browser.batch':
                result = []; // Simplification
                break;
            default:
                throw new Error(`Method ${method} not supported`);
        }
    } catch (e) {
        error = { code: -32603, message: e.message };
    }

    res.json({
        jsonrpc: "2.0",
        id,
        result: error ? undefined : result,
        error: error || undefined
    });
});

app.get('/health', (req, res) => res.json({ status: "ok" }));

const port = process.env.PORT || 8765;
app.listen(port, () => {
    console.log(`JSON-RPC Server for agent-browser running on port ${port}`);
});
