"""Exercise actual browser functions with synthetic DOM/transport/storage."""

import shutil
import subprocess
from pathlib import Path

import pytest

HTML = Path(__file__).resolve().parents[1] / "apps" / "rendezvous_web" / "index.html"


def run_node(script):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable.")
    result = subprocess.run(
        [node, "-"],
        input=script,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


def section(begin, end):
    return begin + HTML.read_text(encoding="utf-8").split(begin, 1)[1].split(end, 1)[0]


def test_api_guard_counts_review_and_failure_and_rejects_stale_responses():
    api = section("let pendingApiCalls = 0;", "function post(")
    switch = section("async function applyVault()", "function archiveVaultSession(")
    run_node(
        """
const assert = require('node:assert/strict');
const state = {localClient: true, token: null};
const notices = [];
function setMsg(...args) {notices.push(args);}
function t(key) {return key;}
function response(body, gen=1, vault='a', status=200) {
  return {ok:status===200, status, json:async()=>body,
    headers:new Map([['X-Slowmatch-Generation', String(gen)], ['X-Slowmatch-Vault', vault]])};
}
let finish;
let fetch = async () => new Promise(resolve => {finish = resolve;});
let reviewDisclosure;
"""
        + api
        + switch
        + """
(async () => {
  vaultGeneration = 1; vaultId = 'a';
  const waiting = api('/local/ai/chat');
  assert.equal(pendingApiCalls, 1);
  await applyVault(); // busy switch must not reach DOM/storage/network
  assert.match(notices.at(-1)[1], /Wait for the current request/);
  vaultGeneration = 2; vaultId = 'b';
  finish(response({reply:'old private reply'}));
  await assert.rejects(waiting, /active vault or AI changed/);
  assert.equal(pendingApiCalls, 0);
  fetch = async () => {throw Error('synthetic failure');};
  await assert.rejects(api('/local/ai/chat'), /synthetic failure/);
  assert.equal(pendingApiCalls, 0);
  fetch = async () => response({detail:{code:'disclosure_review_required'}}, 2, 'b', 409);
  let reviewed;
  reviewDisclosure = () => new Promise(resolve => {reviewed = resolve;});
  const reviewing = api('/local/ai/chat');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(pendingApiCalls, 1);
  await applyVault();
  assert.match(notices.at(-1)[1], /Wait for the current request/);
  reviewed(null);
  await assert.rejects(reviewing, /cancelled/);
  assert.equal(pendingApiCalls, 0);
  // An independent browser tab switched the server: do not adopt its vault.
  fetch = async (_path, opts) => {
    assert.equal(opts.headers['X-Slowmatch-Generation'], '2');
    return response({vault_dir:'c'}, 3, 'c');
  };
  await assert.rejects(api('/local/status'), /active vault or AI changed/);
  assert.equal(vaultGeneration, 2); assert.equal(vaultId, 'b');
  assert.equal(pendingApiCalls, 0);
})().catch(error => {console.error(error); process.exitCode = 1;});
"""
    )


def test_vault_switch_archives_session_and_clears_only_active_context():
    switch = section("async function applyVault()", "async function refreshDataList(")
    reset = section(
        "function resetSession(message)",
        "/* ------------------------------------------------------------------ api */",
    )
    cards = section("function saveMyCard(card)", "function setLocked(")
    identity = section("function loadIdentity()", "function randomPseudonym(")
    run_node(
        """
const assert = require('node:assert/strict');
const storage = new Map([
  ['sm_chat','old chat'], ['unrelated','keep'], ['sm_matchlog','old matches']]);
const sessionStorage = {getItem:key=>storage.get(key), setItem:(key,value)=>storage.set(key,value),
  removeItem:key=>storage.delete(key)};
const cached = new Map([['slowmatch_card::__device','old device card']]);
const localStorage = {setItem:(key,value)=>cached.set(key,value), getItem:key=>cached.get(key)};
const elements = new Map();
const document = {getElementById(id) {
  if (!elements.has(id)) elements.set(id, {value: id==='sourceNotes' ? 'unsaved notes' : '',
    textContent:'old report', checked:true, classList:{add(){},toggle(){}}});
  return elements.get(id);
}};
let chatHistory = [{role:'user',content:'synthetic old chat'}];
const state = {localClient:true, savedCard:{old:true}, savedFingerprint:'old', aiName:'old AI',
  pseudonym:'synthetic-a', registered:true, attested:true, token:'synthetic-token',
  nodeUrl:'', geohash:'synthetic', pollTimer:null, matchTimer:null};
let pendingApiCalls = 0, vaultSwitching = false, vaultId = 'a';
function validateCompatibilityCard(card) {return card;}
function refreshMatchGates(){} function setLocked(){} function renderChatStatus(){}
function renderReport(){} function renderDeepReport(report){state.lastDeepReport=report;}
function persistChat(){sessionStorage.setItem('sm_chat',JSON.stringify(chatHistory));}
function setMsg(){} function t(key){return key;}
async function refreshDataList(){} async function refreshDashboard(){}
let modelRefreshes = 0;
async function refreshModelOptions(value){assert.equal(value,''); modelRefreshes++;}
async function post(){vaultId='b'; return {data_files:0};}
async function api(){return {profile:null};}
"""
        + reset
        + cards
        + identity
        + switch
        + """
(async () => {
  await applyVault();
  assert.equal(vaultSwitching, false);
  assert.equal(modelRefreshes, 1);
  assert.equal(state.savedCard, null); assert.equal(loadMyCard(), null);
  assert.equal(state.token, null); assert.equal(state.aiName, null);
  assert.deepEqual(loadIdentity(), {});
  assert.deepEqual(chatHistory, []); assert.equal(storage.get('sm_chat'), '[]');
  assert.equal(storage.get('unrelated'), 'keep');
  assert.equal(cached.get('slowmatch_card::__device'), 'old device card');
  assert.equal(storage.get('sm_vault_id'), 'b');
  const key = [...storage.keys()].find(key => key.startsWith('sm_vault_session::a::'));
  const archive = JSON.parse(storage.get(key));
  assert.equal(archive.chat[0].content, 'synthetic old chat');
  assert.equal(archive.token, 'synthetic-token');
  assert.equal(archive.drafts.sourceNotes, 'unsaved notes');
  assert.equal(archive.matchLog, 'old matches');
  assert.equal(document.getElementById('sourceNotes').value, '');
  for (const id of ['sourceCount','generateMsg','generateMsg2','deepMsg','reportBox']) {
    assert.equal(document.getElementById(id).textContent, '');
  }
  assert.equal(document.getElementById('consent').checked, false);
  post = async () => {throw Error('synthetic switch failure');};
  await applyVault();
  assert.equal(vaultSwitching, false);
})().catch(error => {console.error(error); process.exitCode = 1;});
"""
    )


def test_local_default_and_unverified_cli_choices_are_not_available():
    html = HTML.read_text(encoding="utf-8")
    assert '<option value="ollama" data-i18n="backendOllama" selected>' in html
    for backend in ["codex", "gemini"]:
        tag = '<option value="' + backend + '"'
        assert "disabled" in html.split(tag, 1)[1].split(">", 1)[0]
