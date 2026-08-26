#!/usr/bin/env python3
"""
Famly Learning Journey Downloader 🌈
=====================================

Downloads every photo, video, and document from your child's Famly
learning journey and builds a beautiful browsable gallery (index.html)
you can keep forever — even after your child leaves the nursery.

USAGE
-----
    python3 famly-download.py --token TOKEN --installation-id ID --child-id CHILD_ID

(See the step-by-step instructions below to get those three values.)

REQUIREMENTS
-----------
    • macOS with Python 3 (already installed on every Mac since 2019)
    • A web browser (Chrome, Safari, Firefox, or Edge — any will do)
    • 5 minutes

If you hit a snag, reach out to whoever shared this script with you —
they've run this before and can help.
"""

import argparse
import base64
import html
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# ──────────────────────────────────────────────────────────────────────
# Step-by-step instructions (shown when run with --help or no args)
# ──────────────────────────────────────────────────────────────────────

INSTRUCTIONS = """
════════════════════════════════════════════════════════════════════════
  HOW TO GET YOUR THREE VALUES  (takes ~3 minutes, do this once)
════════════════════════════════════════════════════════════════════════

You need three things: your TOKEN, your INSTALLATION ID, and your
CHILD ID. All three come from the same place — your browser's DevTools
while logged in to Famly. Here's exactly how, step by step.

────────────────────────────────────────────────────────────────────────
  STEP 1 — Open your child's learning journey page
────────────────────────────────────────────────────────────────────────

  1. Open your web browser and go to app.famly.co
  2. Log in (if you aren't already)
  3. Navigate to your child's profile → the "Learning Journey" tab

  ➜ The web address (URL) at the top of your browser will look like:

      https://app.famly.co/#/account/childProfile/THIS-LONG-ID/childProfileLearningJourney

  ✦ The "THIS-LONG-ID" part is your CHILD ID.
    It's a string of letters and numbers with dashes, like:
        a1b2c3d4-e5f6-7890-abcd-ef1234567890
    Copy it somewhere safe (Notes app, a text file — anywhere).

────────────────────────────────────────────────────────────────────────
  STEP 2 — Open the browser's "inspector" (DevTools)
────────────────────────────────────────────────────────────────────────

  We need to see the hidden "request headers" your browser sends to
  Famly. Don't worry — this is just viewing, you won't change anything.

  ⑴  Make sure you're on the Learning Journey page (from Step 1)

  ⑵  Right-click anywhere on the page → click "Inspect"
      (In Safari, you may first need to enable this: Safari menu →
       Settings → Advanced → tick "Show Develop menu in menu bar",
       then Develop menu → "Show Web Inspector")

  ⑶  A panel opens (usually at the bottom or right side). At its top,
      click the "Network" tab.

  ⑷  If there's a round "recording" button (🔴), make sure it's red
      (click it if it's grey). Then refresh the page (⌘+R or F5).

  ⑸  In the Network list, you'll see lots of entries. You want one
      named "graphql" — type "graphql" into the search/filter box to
      narrow it down.

  ⑹  Click any "graphql" entry. A new panel appears on the right.

  ⑺  In that panel, click "Headers" (or "Request Headers").

  ⑻  Scroll down to the "Request Headers" section. You'll see a list
      of headers like "content-type", "accept", etc. Look for three
      specific ones:

      ┌──────────────────────────────────────────────────────────────┐
      │  x-famly-accesstoken :  <a long string ending in lots of letters/numbers> │
      │  x-famly-installationid:  <a string with dashes, like a UUID>   │
      │  x-famly-platform :  docker                                    │
      └──────────────────────────────────────────────────────────────┘

  ✦ The value next to "x-famly-accesstoken" is your TOKEN.
  ✦ The value next to "x-famly-installationid" is your INSTALLATION ID.

  Copy both values (double-click the value to select it, then ⌘+C).

  Tip: The TOKEN usually looks like a string of letters and numbers
       (about 36 characters, with dashes — like a UUID).
       The INSTALLATION ID is also a UUID (same format).

────────────────────────────────────────────────────────────────────────
  STEP 3 — Run this script
────────────────────────────────────────────────────────────────────────

  Open the Terminal app (⌘+Space, type "Terminal", press Enter).
  Navigate to wherever you saved this file, then run:

      python3 famly-download.py \\
        --token "YOUR-TOKEN-HERE" \\
        --installation-id "YOUR-INSTALLATION-ID-HERE" \\
        --child-id "YOUR-CHILD-ID-HERE"

  Replace the three values with the ones you copied. Keep the quotes
  around each one. The backslashes (\\) are just line breaks for
  readability — you can also put it all on one line:

      python3 famly-download.py --token "T" --installation-id "I" --child-id "C"

  That's it! The script will:
    1. Connect to Famly and fetch every observation from your child's
       learning journey (this can take 10-30 seconds).
    2. Download every photo, video, and document into a folder
       named "famly-archive" (next to this script).
    3. Build a "gallery" web page (index.html) you can open in your
       browser to browse everything by date — even offline.
    4. Open the gallery for you automatically.

  ⚠️  TIMING: The download URLs from Famly expire after ~24 hours, so
      run this all in one sitting. If you stop and come back the next
      day, you'll need to get a fresh TOKEN from Step 2 again (the
      INSTALLATION ID and CHILD ID stay the same).

  💡  UPDATING THE GALLERY LATER: Once you've run the full download
      once, you can refresh the gallery (to pick up script updates or
      style changes) WITHOUT needing your token or any auth:

      python3 famly-download.py --gallery-only

      This reads the saved manifest.json and rebuilds index.html in
      seconds. Add --output-dir if your archive is elsewhere.

  💡  SHARING AS A SINGLE FILE: Want to send the whole gallery to a
      grandparent or partner as one file — no folder needed? Add
      --embed and everything (photos, PDFs, and optionally videos)
      gets packed inside the HTML as data URIs:

      python3 famly-download.py --gallery-only --embed

      The result is a single ~30-100 MB HTML file that works on its
      own. It also adds a "Download all as ZIP" button so the
      recipient can extract the original files for safekeeping.

      Videos are the bulk of the size. Use --embed-no-videos for a
      lighter ~30 MB file (videos show a placeholder instead):

      python3 famly-download.py --gallery-only --embed --embed-no-videos

────────────────────────────────────────────────────────────────────────
  TROUBLESHOOTING
────────────────────────────────────────────────────────────────────────

  ✗ "Not authorized" or empty results
    → Your TOKEN may have expired (they're temporary). Redo Step 2 to
      get a fresh one. The token usually lasts a few hours to a day.

  ✗ "Child not found" or no observations
    → Double-check the CHILD ID from Step 1 — it must match exactly,
      including all dashes. Make sure you copied the full ID, not just
      the first part.

  ✗ Can't find "graphql" in the Network tab
    → Make sure you refreshed the page (⌘+R) AFTER opening the Network
      tab. The requests only show up while the tab is recording.

  ✗ Can't find the x-famly-* headers
    → You may be looking at "Response Headers" instead of "Request
      Headers". Scroll to the section labelled "Request Headers" (it's
      usually lower down). In some browsers it's under a "Headers"
      sub-tab within the request panel.

  ✗ "python3: command not found"
    → On older Macs, try `python` instead of `python3`. Or install
      Python 3 from python.org (free).

  ✗ Nothing happens / script hangs
    → The first run can take 30-60 seconds for lots of photos. Wait.
      If it's truly stuck after a few minutes, press Ctrl+C and try
      again — already-downloaded files are skipped.

════════════════════════════════════════════════════════════════════════
  PRIVACY NOTES
════════════════════════════════════════════════════════════════════════

  • Your TOKEN is like a temporary password — it lets this script
    access YOUR child's data only. It doesn't give access to any
    other child or family.
  • This script only talks to app.famly.co — it doesn't send your
    data anywhere else. Everything stays on your Mac.
  • Once the download finishes, you can throw away the TOKEN — the
    downloaded files don't need it. (The TOKEN expires on its own
    within a day anyway.)
  • Share this script freely with other parents. Don't share your
    TOKEN or CHILD ID — those are yours alone.

════════════════════════════════════════════════════════════════════════
"""


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

GRAPHQL_URL = "https://app.famly.co/graphql"
DEFAULT_OUTPUT_DIR = "famly-archive"
MAX_DOWNLOAD_WORKERS = 8  # parallel downloads
PAGE_SIZE = 100            # observations per GraphQL page
MAX_PAGES = 200            # safety cap (100 obs/page = 20,000 obs max)


# ──────────────────────────────────────────────────────────────────────
# Inlined fflate (zip library) — used only in --embed mode
# ──────────────────────────────────────────────────────────────────────
# fflate by Tarreon (https://github.com/101arrowz/fflate), MIT License.
# Inlined so the script stays zero-dependency even for --embed (no CDN fetch).
# The browser uses it only when the user clicks "Download all as ZIP".
FFLATE_JS = r"""
!function(f){typeof module!='undefined'&&typeof exports=='object'?module.exports=f():typeof define!='undefined'&&define.amd?define(f):(typeof self!='undefined'?self:this).fflate=f()}(function(){var _e={};"use strict";var t=(typeof module!='undefined'&&typeof exports=='object'?function(_f){"use strict";var e,t=";var __w=require('worker_threads');__w.parentPort.on('message',function(m){onmessage({data:m})}),postMessage=function(m,t){__w.parentPort.postMessage(m,t)},close=process.exit;self=global";try{e=require("worker_threads").Worker}catch(e){}exports.default=e?function(r,n,o,a,s){var u=!1,i=new e(r+t,{eval:!0}).on("error",(function(e){return s(e,null)})).on("message",(function(e){return s(null,e)})).on("exit",(function(e){e&&!u&&s(Error("exited with code "+e),null)}));return i.postMessage(o,a),i.terminate=function(){return u=!0,e.prototype.terminate.call(i)},i}:function(e,t,r,n,o){setImmediate((function(){return o(Error("async operations unsupported - update to Node 12+ (or Node 10-11 with the --experimental-worker CLI flag)"),null)}));var a=function(){};return{terminate:a,postMessage:a}};return _f}:function(_f){"use strict";var e={};_f.default=function(r,t,s,a,n){var o=new Worker(e[t]||(e[t]=URL.createObjectURL(new Blob([r+';addEventListener("error",function(e){e=e.error;postMessage({$e$:[e.message,e.code,e.stack]})})'],{type:"text/javascript"}))));return o.onmessage=function(e){var r=e.data,t=r.$e$;if(t){var s=Error(t[0]);s.code=t[1],s.stack=t[2],n(s,null)}else n(null,r)},o.postMessage(s,a),o};return _f})({}),n=Uint8Array,r=Uint16Array,e=Int32Array,i=new n([0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0]),o=new n([0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0]),s=new n([16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]),a=function(t,n){for(var i=new r(31),o=0;o<31;++o)i[o]=n+=1<<t[o-1];var s=new e(i[30]);for(o=1;o<30;++o)for(var a=i[o];a<i[o+1];++a)s[a]=a-i[o]<<5|o;return{b:i,r:s}},u=a(i,2),h=u.b,f=u.r;h[28]=258,f[258]=28;for(var l=a(o,0),c=l.b,p=l.r,v=new r(32768),d=0;d<32768;++d){var g=(43690&d)>>1|(21845&d)<<1;v[d]=((65280&(g=(61680&(g=(52428&g)>>2|(13107&g)<<2))>>4|(3855&g)<<4))>>8|(255&g)<<8)>>1}var y=function(t,n,e){for(var i=t.length,o=0,s=new r(n);o<i;++o)t[o]&&++s[t[o]-1];var a,u=new r(n);for(o=1;o<n;++o)u[o]=u[o-1]+s[o-1]<<1;if(e){a=new r(1<<n);var h=15-n;for(o=0;o<i;++o)if(t[o])for(var f=o<<4|t[o],l=n-t[o],c=u[t[o]-1]++<<l,p=c|(1<<l)-1;c<=p;++c)a[v[c]>>h]=f}else for(a=new r(i),o=0;o<i;++o)t[o]&&(a[o]=v[u[t[o]-1]++]>>15-t[o]);return a},m=new n(288);for(d=0;d<144;++d)m[d]=8;for(d=144;d<256;++d)m[d]=9;for(d=256;d<280;++d)m[d]=7;for(d=280;d<288;++d)m[d]=8;var b=new n(32);for(d=0;d<32;++d)b[d]=5;var w=y(m,9,0),x=y(m,9,1),z=y(b,5,0),k=y(b,5,1),M=function(t){for(var n=t[0],r=1;r<t.length;++r)t[r]>n&&(n=t[r]);return n},S=function(t,n,r){var e=n/8|0;return(t[e]|t[e+1]<<8)>>(7&n)&r},A=function(t,n){var r=n/8|0;return(t[r]|t[r+1]<<8|t[r+2]<<16)>>(7&n)},T=function(t){return(t+7)/8|0},D=function(t,r,e){return(null==r||r<0)&&(r=0),(null==e||e>t.length)&&(e=t.length),new n(t.subarray(r,e))};_e.FlateErrorCode={UnexpectedEOF:0,InvalidBlockType:1,InvalidLengthLiteral:2,InvalidDistance:3,StreamFinished:4,NoStreamHandler:5,InvalidHeader:6,NoCallback:7,InvalidUTF8:8,ExtraFieldTooLong:9,InvalidDate:10,FilenameTooLong:11,StreamFinishing:12,InvalidZipData:13,UnknownCompressionMethod:14};var C=["unexpected EOF","invalid block type","invalid length/literal","invalid distance","stream finished","no stream handler",,"no callback","invalid UTF-8 data","extra field too long","date not in range 1980-2099","filename too long","stream finishing","invalid zip data"],I=function(t,n,r){var e=Error(n||C[t]);if(e.code=t,Error.captureStackTrace&&Error.captureStackTrace(e,I),!r)throw e;return e},U=function(t,r,e,a){var u=t.length,f=a?a.length:0;if(!u||r.f&&!r.l)return e||new n(0);var l=!e,p=l||2!=r.i,v=r.i;l&&(e=new n(3*u));var d=function(t){var r=e.length;if(t>r){var i=new n(Math.max(2*r,t));i.set(e),e=i}},g=r.f||0,m=r.p||0,b=r.b||0,w=r.l,z=r.d,C=r.m,U=r.n,F=8*u;do{if(!w){g=S(t,m,1);var E=S(t,m+1,3);if(m+=3,!E){var Z=t[(J=T(m)+4)-4]|t[J-3]<<8,q=J+Z;if(q>u){v&&I(0);break}p&&d(b+Z),e.set(t.subarray(J,q),b),r.b=b+=Z,r.p=m=8*q,r.f=g;continue}if(1==E)w=x,z=k,C=9,U=5;else if(2==E){var O=S(t,m,31)+257,G=S(t,m+10,15)+4,L=O+S(t,m+5,31)+1;m+=14;for(var H=new n(L),j=new n(19),N=0;N<G;++N)j[s[N]]=S(t,m+3*N,7);m+=3*G;var P=M(j),B=(1<<P)-1,Y=y(j,P,1);for(N=0;N<L;){var J,K=Y[S(t,m,B)];if(m+=15&K,(J=K>>4)<16)H[N++]=J;else{var Q=0,R=0;for(16==J?(R=3+S(t,m,3),m+=2,Q=H[N-1]):17==J?(R=3+S(t,m,7),m+=3):18==J&&(R=11+S(t,m,127),m+=7);R--;)H[N++]=Q}}var V=H.subarray(0,O),W=H.subarray(O);C=M(V),U=M(W),w=y(V,C,1),z=y(W,U,1)}else I(1);if(m>F){v&&I(0);break}}p&&d(b+131072);for(var X=(1<<C)-1,$=(1<<U)-1,_=m;;_=m){var tt=(Q=w[A(t,m)&X])>>4;if((m+=15&Q)>F){v&&I(0);break}if(Q||I(2),tt<256)e[b++]=tt;else{if(256==tt){_=m,w=null;break}var nt=tt-254;tt>264&&(nt=S(t,m,(1<<(it=i[N=tt-257]))-1)+h[N],m+=it);var rt=z[A(t,m)&$],et=rt>>4;if(rt||I(3),m+=15&rt,W=c[et],et>3){var it=o[et];W+=A(t,m)&(1<<it)-1,m+=it}if(m>F){v&&I(0);break}p&&d(b+131072);var ot=b+nt;if(b<W){var st=f-W,at=Math.min(W,ot);for(st+b<0&&I(3);b<at;++b)e[b]=a[st+b]}for(;b<ot;++b)e[b]=e[b-W]}}r.l=w,r.p=_,r.b=b,r.f=g,w&&(g=1,r.m=C,r.d=z,r.n=U)}while(!g);return b!=e.length&&l?D(e,0,b):e.subarray(0,b)},F=function(t,n,r){var e=n/8|0;t[e]|=r<<=7&n,t[e+1]|=r>>8},E=function(t,n,r){var e=n/8|0;t[e]|=r<<=7&n,t[e+1]|=r>>8,t[e+2]|=r>>16},Z=function(t,e){for(var i=[],o=0;o<t.length;++o)t[o]&&i.push({s:o,f:t[o]});var s=i.length,a=i.slice();if(!s)return{t:N,l:0};if(1==s){var u=new n(i[0].s+1);return u[i[0].s]=1,{t:u,l:1}}i.sort((function(t,n){return t.f-n.f})),i.push({s:-1,f:25001});var h=i[0],f=i[1],l=0,c=1,p=2;for(i[0]={s:-1,f:h.f+f.f,l:h,r:f};c!=s-1;)h=i[i[l].f<i[p].f?l++:p++],f=i[l!=c&&i[l].f<i[p].f?l++:p++],i[c++]={s:-1,f:h.f+f.f,l:h,r:f};var v=a[0].s;for(o=1;o<s;++o)a[o].s>v&&(v=a[o].s);var d=new r(v+1),g=q(i[c-1],d,0);if(g>e){o=0;var y=0,m=g-e,b=1<<m;for(a.sort((function(t,n){return d[n.s]-d[t.s]||t.f-n.f}));o<s;++o){var w=a[o].s;if(!(d[w]>e))break;y+=b-(1<<g-d[w]),d[w]=e}for(y>>=m;y>0;){var x=a[o].s;d[x]<e?y-=1<<e-d[x]++-1:++o}for(;o>=0&&y;--o){var z=a[o].s;d[z]==e&&(--d[z],++y)}g=e}return{t:new n(d),l:g}},q=function(t,n,r){return-1==t.s?Math.max(q(t.l,n,r+1),q(t.r,n,r+1)):n[t.s]=r},O=function(t){for(var n=t.length;n&&!t[--n];);for(var e=new r(++n),i=0,o=t[0],s=1,a=function(t){e[i++]=t},u=1;u<=n;++u)if(t[u]==o&&u!=n)++s;else{if(!o&&s>2){for(;s>138;s-=138)a(32754);s>2&&(a(s>10?s-11<<5|28690:s-3<<5|12305),s=0)}else if(s>3){for(a(o),--s;s>6;s-=6)a(8304);s>2&&(a(s-3<<5|8208),s=0)}for(;s--;)a(o);s=1,o=t[u]}return{c:e.subarray(0,i),n:n}},G=function(t,n){for(var r=0,e=0;e<n.length;++e)r+=t[e]*n[e];return r},L=function(t,n,r){var e=r.length,i=T(n+2);t[i]=255&e,t[i+1]=e>>8,t[i+2]=255^t[i],t[i+3]=255^t[i+1];for(var o=0;o<e;++o)t[i+o+4]=r[o];return 8*(i+4+e)},H=function(t,n,e,a,u,h,f,l,c,p,v){F(n,v++,e),++u[256];for(var d=Z(u,15),g=d.t,x=d.l,k=Z(h,15),M=k.t,S=k.l,A=O(g),T=A.c,D=A.n,C=O(M),I=C.c,U=C.n,q=new r(19),H=0;H<T.length;++H)++q[31&T[H]];for(H=0;H<I.length;++H)++q[31&I[H]];for(var j=Z(q,7),N=j.t,P=j.l,B=19;B>4&&!N[s[B-1]];--B);var Y,J,K,Q,R=p+5<<3,V=G(u,m)+G(h,b)+f,W=G(u,g)+G(h,M)+f+14+3*B+G(q,N)+2*q[16]+3*q[17]+7*q[18];if(c>=0&&R<=V&&R<=W)return L(n,v,t.subarray(c,c+p));if(F(n,v,1+(W<V)),v+=2,W<V){Y=y(g,x,0),J=g,K=y(M,S,0),Q=M;var X=y(N,P,0);for(F(n,v,D-257),F(n,v+5,U-1),F(n,v+10,B-4),v+=14,H=0;H<B;++H)F(n,v+3*H,N[s[H]]);v+=3*B;for(var $=[T,I],_=0;_<2;++_){var tt=$[_];for(H=0;H<tt.length;++H)F(n,v,X[rt=31&tt[H]]),v+=N[rt],rt>15&&(F(n,v,tt[H]>>5&127),v+=tt[H]>>12)}}else Y=w,J=m,K=z,Q=b;for(H=0;H<l;++H){var nt=a[H];if(nt>255){var rt;E(n,v,Y[257+(rt=nt>>18&31)]),v+=J[rt+257],rt>7&&(F(n,v,nt>>23&31),v+=i[rt]);var et=31&nt;E(n,v,K[et]),v+=Q[et],et>3&&(E(n,v,nt>>5&8191),v+=o[et])}else E(n,v,Y[nt]),v+=J[nt]}return E(n,v,Y[256]),v+J[256]},j=new e([65540,131080,131088,131104,262176,1048704,1048832,2114560,2117632]),N=new n(0),P=function(t,s,a,u,h,l){var c=l.z||t.length,v=new n(u+c+5*(1+Math.ceil(c/7e3))+h),d=v.subarray(u,v.length-h),g=l.l,y=7&(l.r||0);if(s){y&&(d[0]=l.r>>3);for(var m=j[s-1],b=m>>13,w=8191&m,x=(1<<a)-1,z=l.p||new r(32768),k=l.h||new r(x+1),M=Math.ceil(a/3),S=2*M,A=function(n){return(t[n]^t[n+1]<<M^t[n+2]<<S)&x},C=new e(25e3),I=new r(288),U=new r(32),F=0,E=0,Z=l.i||0,q=0,O=l.w||0,G=0;Z+2<c;++Z){var N=A(Z),P=32767&Z,B=k[N];if(z[P]=B,k[N]=P,O<=Z){var Y=c-Z;if((F>7e3||q>24576)&&(Y>423||!g)){y=H(t,d,0,C,I,U,E,q,G,Z-G,y),q=F=E=0,G=Z;for(var J=0;J<286;++J)I[J]=0;for(J=0;J<30;++J)U[J]=0}var K=2,Q=0,R=w,V=P-B&32767;if(Y>2&&N==A(Z-V))for(var W=Math.min(b,Y)-1,X=Math.min(32767,Z),$=Math.min(258,Y);V<=X&&--R&&P!=B;){if(t[Z+K]==t[Z+K-V]){for(var _=0;_<$&&t[Z+_]==t[Z+_-V];++_);if(_>K){if(K=_,Q=V,_>W)break;var tt=Math.min(V,_-2),nt=0;for(J=0;J<tt;++J){var rt=Z-V+J&32767,et=rt-z[rt]&32767;et>nt&&(nt=et,B=rt)}}}V+=(P=B)-(B=z[P])&32767}if(Q){C[q++]=268435456|f[K]<<18|p[Q];var it=31&f[K],ot=31&p[Q];E+=i[it]+o[ot],++I[257+it],++U[ot],O=Z+K,++F}else C[q++]=t[Z],++I[t[Z]]}}for(Z=Math.max(Z,O);Z<c;++Z)C[q++]=t[Z],++I[t[Z]];y=H(t,d,g,C,I,U,E,q,G,Z-G,y),g||(l.r=7&y|d[y/8|0]<<3,y-=7,l.h=k,l.p=z,l.i=Z,l.w=O)}else{for(Z=l.w||0;Z<c+g;Z+=65535){var st=Z+65535;st>=c&&(d[y/8|0]=g,st=c),y=L(d,y+1,t.subarray(Z,st))}l.i=c}return D(v,0,u+T(y)+h)},B=function(){for(var t=new Int32Array(256),n=0;n<256;++n){for(var r=n,e=9;--e;)r=(1&r&&-306674912)^r>>>1;t[n]=r}return t}(),Y=function(){var t=-1;return{p:function(n){for(var r=t,e=0;e<n.length;++e)r=B[255&r^n[e]]^r>>>8;t=r},d:function(){return~t}}},J=function(){var t=1,n=0;return{p:function(r){for(var e=t,i=n,o=0|r.length,s=0;s!=o;){for(var a=Math.min(s+2655,o);s<a;++s)i+=e+=r[s];e=(65535&e)+15*(e>>16),i=(65535&i)+15*(i>>16)}t=e,n=i},d:function(){return(255&(t%=65521))<<24|(65280&t)<<8|(255&(n%=65521))<<8|n>>8}}},K=function(t,r,e,i,o){if(!o&&(o={l:1},r.dictionary)){var s=r.dictionary.subarray(-32768),a=new n(s.length+t.length);a.set(s),a.set(t,s.length),t=a,o.w=s.length}return P(t,null==r.level?6:r.level,null==r.mem?o.l?Math.ceil(1.5*Math.max(8,Math.min(13,Math.log(t.length)))):20:12+r.mem,e,i,o)},Q=function(t,n){var r={};for(var e in t)r[e]=t[e];for(var e in n)r[e]=n[e];return r},R=function(t,n,r){for(var e=t(),i=""+t,o=i.slice(i.indexOf("[")+1,i.lastIndexOf("]")).replace(/\s+/g,"").split(","),s=0;s<e.length;++s){var a=e[s],u=o[s];if("function"==typeof a){n+=";"+u+"=";var h=""+a;if(a.prototype)if(-1!=h.indexOf("[native code]")){var f=h.indexOf(" ",8)+1;n+=h.slice(f,h.indexOf("(",f))}else for(var l in n+=h,a.prototype)n+=";"+u+".prototype."+l+"="+a.prototype[l];else n+=h}else r[u]=a}return n},V=[],W=function(t){var n=[];for(var r in t)t[r].buffer&&n.push((t[r]=new t[r].constructor(t[r])).buffer);return n},X=function(n,r,e,i){if(!V[e]){for(var o="",s={},a=n.length-1,u=0;u<a;++u)o=R(n[u],o,s);V[e]={c:R(n[a],o,s),e:s}}var h=Q({},V[e].e);return(0,t.default)(V[e].c+";onmessage=function(e){for(var k in e.data)self[k]=e.data[k];onmessage="+r+"}",e,h,W(h),i)},$=function(){return[n,r,e,i,o,s,h,c,x,k,v,C,y,M,S,A,T,D,I,U,Tt,it,ot]},_=function(){return[n,r,e,i,o,s,f,p,w,m,z,b,v,j,N,y,F,E,Z,q,O,G,L,H,T,D,P,K,kt,it]},tt=function(){return[pt,gt,ct,Y,B]},nt=function(){return[vt,dt]},rt=function(){return[yt,ct,J]},et=function(){return[mt]},it=function(t){return postMessage(t,[t.buffer])},ot=function(t){return t&&{out:t.size&&new n(t.size),dictionary:t.dictionary}},st=function(t,n,r,e,i,o){var s=X(r,e,i,(function(t,n){s.terminate(),o(t,n)}));return s.postMessage([t,n],n.consume?[t.buffer]:[]),function(){s.terminate()}},at=function(t){return t.ondata=function(t,n){return postMessage([t,n],[t.buffer])},function(n){n.data.length?(t.push(n.data[0],n.data[1]),postMessage([n.data[0].length])):t.flush()}},ut=function(t,n,r,e,i,o,s){var a,u=X(t,e,i,(function(t,r){t?(u.terminate(),n.ondata.call(n,t)):Array.isArray(r)?1==r.length?(n.queuedSize-=r[0],n.ondrain&&n.ondrain(r[0])):(r[1]&&u.terminate(),n.ondata.call(n,t,r[0],r[1])):s(r)}));u.postMessage(r),n.queuedSize=0,n.push=function(t,r){n.ondata||I(5),a&&n.ondata(I(4,0,1),null,!!r),n.queuedSize+=t.length,u.postMessage([t,a=r],[t.buffer])},n.terminate=function(){u.terminate()},o&&(n.flush=function(){u.postMessage([])})},ht=function(t,n){return t[n]|t[n+1]<<8},ft=function(t,n){return(t[n]|t[n+1]<<8|t[n+2]<<16|t[n+3]<<24)>>>0},lt=function(t,n){return ft(t,n)+4294967296*ft(t,n+4)},ct=function(t,n,r){for(;r;++n)t[n]=r,r>>>=8},pt=function(t,n){var r=n.filename;if(t[0]=31,t[1]=139,t[2]=8,t[8]=n.level<2?4:9==n.level?2:0,t[9]=3,0!=n.mtime&&ct(t,4,Math.floor(new Date(n.mtime||Date.now())/1e3)),r){t[3]=8;for(var e=0;e<=r.length;++e)t[e+10]=r.charCodeAt(e)}},vt=function(t){31==t[0]&&139==t[1]&&8==t[2]||I(6,"invalid gzip data");var n=t[3],r=10;4&n&&(r+=2+(t[10]|t[11]<<8));for(var e=(n>>3&1)+(n>>4&1);e>0;e-=!t[r++]);return r+(2&n)},dt=function(t){var n=t.length;return(t[n-4]|t[n-3]<<8|t[n-2]<<16|t[n-1]<<24)>>>0},gt=function(t){return 10+(t.filename?t.filename.length+1:0)},yt=function(t,n){var r=n.level,e=0==r?0:r<6?1:9==r?3:2;if(t[0]=120,t[1]=e<<6|(n.dictionary&&32),t[1]|=31-(t[0]<<8|t[1])%31,n.dictionary){var i=J();i.p(n.dictionary),ct(t,2,i.d())}},mt=function(t,n){return(8!=(15&t[0])||t[0]>>4>7||(t[0]<<8|t[1])%31)&&I(6,"invalid zlib data"),(t[1]>>5&1)==+!n&&I(6,"invalid zlib data: "+(32&t[1]?"need":"unexpected")+" dictionary"),2+(t[1]>>3&4)};function bt(t,n){return"function"==typeof t&&(n=t,t={}),this.ondata=n,t}var wt=function(){function t(t,r){if("function"==typeof t&&(r=t,t={}),this.ondata=r,this.o=t||{},this.s={l:0,i:32768,w:32768,z:32768},this.b=new n(98304),this.o.dictionary){var e=this.o.dictionary.subarray(-32768);this.b.set(e,32768-e.length),this.s.i=32768-e.length}}return t.prototype.p=function(t,n){this.ondata(K(t,this.o,0,0,this.s),n)},t.prototype.push=function(t,r){this.ondata||I(5),this.s.l&&I(4);var e=t.length+this.s.z;if(e>this.b.length){if(e>2*this.b.length-32768){var i=new n(-32768&e);i.set(this.b.subarray(0,this.s.z)),this.b=i}var o=this.b.length-this.s.z;this.b.set(t.subarray(0,o),this.s.z),this.s.z=this.b.length,this.p(this.b,!1),this.b.set(this.b.subarray(-32768)),this.b.set(t.subarray(o),32768),this.s.z=t.length-o+32768,this.s.i=32766,this.s.w=32768}else this.b.set(t,this.s.z),this.s.z+=t.length;this.s.l=1&r,(this.s.z>this.s.w+8191||r)&&(this.p(this.b,r||!1),this.s.w=this.s.i,this.s.i-=2)},t.prototype.flush=function(){this.ondata||I(5),this.s.l&&I(4),this.p(this.b,!1),this.s.w=this.s.i,this.s.i-=2},t}();_e.Deflate=wt;var xt=function(){return function(t,n){ut([_,function(){return[at,wt]}],this,bt.call(this,t,n),(function(t){var n=new wt(t.data);onmessage=at(n)}),6,1)}}();function zt(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[_],(function(t){return it(kt(t.data[0],t.data[1]))}),0,r)}function kt(t,n){return K(t,n||{},0,0)}_e.AsyncDeflate=xt,_e.deflate=zt,_e.deflateSync=kt;var Mt=function(){function t(t,r){"function"==typeof t&&(r=t,t={}),this.ondata=r;var e=t&&t.dictionary&&t.dictionary.subarray(-32768);this.s={i:0,b:e?e.length:0},this.o=new n(32768),this.p=new n(0),e&&this.o.set(e)}return t.prototype.e=function(t){if(this.ondata||I(5),this.d&&I(4),this.p.length){if(t.length){var r=new n(this.p.length+t.length);r.set(this.p),r.set(t,this.p.length),this.p=r}}else this.p=t},t.prototype.c=function(t){this.s.i=+(this.d=t||!1);var n=this.s.b,r=U(this.p,this.s,this.o);this.ondata(D(r,n,this.s.b),this.d),this.o=D(r,this.s.b-32768),this.s.b=this.o.length,this.p=D(this.p,this.s.p/8|0),this.s.p&=7},t.prototype.push=function(t,n){this.e(t),this.c(n)},t}();_e.Inflate=Mt;var St=function(){return function(t,n){ut([$,function(){return[at,Mt]}],this,bt.call(this,t,n),(function(t){var n=new Mt(t.data);onmessage=at(n)}),7,0)}}();function At(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[$],(function(t){return it(Tt(t.data[0],ot(t.data[1])))}),1,r)}function Tt(t,n){return U(t,{i:2},n&&n.out,n&&n.dictionary)}_e.AsyncInflate=St,_e.inflate=At,_e.inflateSync=Tt;var Dt=function(){function t(t,n){this.c=Y(),this.l=0,this.v=1,wt.call(this,t,n)}return t.prototype.push=function(t,n){this.c.p(t),this.l+=t.length,wt.prototype.push.call(this,t,n)},t.prototype.p=function(t,n){var r=K(t,this.o,this.v&&gt(this.o),n&&8,this.s);this.v&&(pt(r,this.o),this.v=0),n&&(ct(r,r.length-8,this.c.d()),ct(r,r.length-4,this.l)),this.ondata(r,n)},t.prototype.flush=function(){wt.prototype.flush.call(this)},t}();_e.Gzip=Dt,_e.Compress=Dt;var Ct=function(){return function(t,n){ut([_,tt,function(){return[at,wt,Dt]}],this,bt.call(this,t,n),(function(t){var n=new Dt(t.data);onmessage=at(n)}),8,1)}}();function It(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[_,tt,function(){return[Ut]}],(function(t){return it(Ut(t.data[0],t.data[1]))}),2,r)}function Ut(t,n){n||(n={});var r=Y(),e=t.length;r.p(t);var i=K(t,n,gt(n),8),o=i.length;return pt(i,n),ct(i,o-8,r.d()),ct(i,o-4,e),i}_e.AsyncGzip=Ct,_e.AsyncCompress=Ct,_e.gzip=It,_e.compress=It,_e.gzipSync=Ut,_e.compressSync=Ut;var Ft=function(){function t(t,n){this.v=1,this.r=0,Mt.call(this,t,n)}return t.prototype.push=function(t,r){if(Mt.prototype.e.call(this,t),this.r+=t.length,this.v){var e=this.p.subarray(this.v-1),i=e.length>3?vt(e):4;if(i>e.length){if(!r)return}else this.v>1&&this.onmember&&this.onmember(this.r-e.length);this.p=e.subarray(i),this.v=0}Mt.prototype.c.call(this,r),!this.s.f||this.s.l||r||(this.v=T(this.s.p)+9,this.s={i:0},this.o=new n(0),this.push(new n(0),r))},t}();_e.Gunzip=Ft;var Et=function(){return function(t,n){var r=this;ut([$,nt,function(){return[at,Mt,Ft]}],this,bt.call(this,t,n),(function(t){var n=new Ft(t.data);n.onmember=function(t){return postMessage(t)},onmessage=at(n)}),9,0,(function(t){return r.onmember&&r.onmember(t)}))}}();function Zt(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[$,nt,function(){return[qt]}],(function(t){return it(qt(t.data[0],t.data[1]))}),3,r)}function qt(t,r){var e=vt(t);return e+8>t.length&&I(6,"invalid gzip data"),U(t.subarray(e,-8),{i:2},r&&r.out||new n(dt(t)),r&&r.dictionary)}_e.AsyncGunzip=Et,_e.gunzip=Zt,_e.gunzipSync=qt;var Ot=function(){function t(t,n){this.c=J(),this.v=1,wt.call(this,t,n)}return t.prototype.push=function(t,n){this.c.p(t),wt.prototype.push.call(this,t,n)},t.prototype.p=function(t,n){var r=K(t,this.o,this.v&&(this.o.dictionary?6:2),n&&4,this.s);this.v&&(yt(r,this.o),this.v=0),n&&ct(r,r.length-4,this.c.d()),this.ondata(r,n)},t.prototype.flush=function(){wt.prototype.flush.call(this)},t}();_e.Zlib=Ot;var Gt=function(){return function(t,n){ut([_,rt,function(){return[at,wt,Ot]}],this,bt.call(this,t,n),(function(t){var n=new Ot(t.data);onmessage=at(n)}),10,1)}}();function Lt(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[_,rt,function(){return[Ht]}],(function(t){return it(Ht(t.data[0],t.data[1]))}),4,r)}function Ht(t,n){n||(n={});var r=J();r.p(t);var e=K(t,n,n.dictionary?6:2,4);return yt(e,n),ct(e,e.length-4,r.d()),e}_e.AsyncZlib=Gt,_e.zlib=Lt,_e.zlibSync=Ht;var jt=function(){function t(t,n){Mt.call(this,t,n),this.v=t&&t.dictionary?2:1}return t.prototype.push=function(t,n){if(Mt.prototype.e.call(this,t),this.v){if(this.p.length<6&&!n)return;this.p=this.p.subarray(mt(this.p,this.v-1)),this.v=0}n&&(this.p.length<4&&I(6,"invalid zlib data"),this.p=this.p.subarray(0,-4)),Mt.prototype.c.call(this,n)},t}();_e.Unzlib=jt;var Nt=function(){return function(t,n){ut([$,et,function(){return[at,Mt,jt]}],this,bt.call(this,t,n),(function(t){var n=new jt(t.data);onmessage=at(n)}),11,0)}}();function Pt(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),st(t,n,[$,et,function(){return[Bt]}],(function(t){return it(Bt(t.data[0],ot(t.data[1])))}),5,r)}function Bt(t,n){return U(t.subarray(mt(t,n&&n.dictionary),-4),{i:2},n&&n.out,n&&n.dictionary)}_e.AsyncUnzlib=Nt,_e.unzlib=Pt,_e.unzlibSync=Bt;var Yt=function(){function t(t,n){this.o=bt.call(this,t,n)||{},this.G=Ft,this.I=Mt,this.Z=jt}return t.prototype.i=function(){var t=this;this.s.ondata=function(n,r){t.ondata(n,r)}},t.prototype.push=function(t,r){if(this.ondata||I(5),this.s)this.s.push(t,r);else{if(this.p&&this.p.length){var e=new n(this.p.length+t.length);e.set(this.p),e.set(t,this.p.length)}else this.p=t;this.p.length>2&&(this.s=31==this.p[0]&&139==this.p[1]&&8==this.p[2]?new this.G(this.o):8!=(15&this.p[0])||this.p[0]>>4>7||(this.p[0]<<8|this.p[1])%31?new this.I(this.o):new this.Z(this.o),this.i(),this.s.push(this.p,r),this.p=null)}},t}();_e.Decompress=Yt;var Jt=function(){function t(t,n){Yt.call(this,t,n),this.queuedSize=0,this.G=Et,this.I=St,this.Z=Nt}return t.prototype.i=function(){var t=this;this.s.ondata=function(n,r,e){t.ondata(n,r,e)},this.s.ondrain=function(n){t.queuedSize-=n,t.ondrain&&t.ondrain(n)}},t.prototype.push=function(t,n){this.queuedSize+=t.length,Yt.prototype.push.call(this,t,n)},t}();function Kt(t,n,r){return r||(r=n,n={}),"function"!=typeof r&&I(7),31==t[0]&&139==t[1]&&8==t[2]?Zt(t,n,r):8!=(15&t[0])||t[0]>>4>7||(t[0]<<8|t[1])%31?At(t,n,r):Pt(t,n,r)}function Qt(t,n){return 31==t[0]&&139==t[1]&&8==t[2]?qt(t,n):8!=(15&t[0])||t[0]>>4>7||(t[0]<<8|t[1])%31?Tt(t,n):Bt(t,n)}_e.AsyncDecompress=Jt,_e.decompress=Kt,_e.decompressSync=Qt;var Rt=function(t,r,e,i){for(var o in t){var s=t[o],a=r+o,u=i;Array.isArray(s)&&(u=Q(i,s[1]),s=s[0]),s instanceof n?e[a]=[s,u]:(e[a+="/"]=[new n(0),u],Rt(s,a,e,i))}},Vt="undefined"!=typeof TextEncoder&&new TextEncoder,Wt="undefined"!=typeof TextDecoder&&new TextDecoder,Xt=0;try{Wt.decode(N,{stream:!0}),Xt=1}catch(t){}var $t=function(t){for(var n="",r=0;;){var e=t[r++],i=(e>127)+(e>223)+(e>239);if(r+i>t.length)return{s:n,r:D(t,r-1)};i?3==i?(e=((15&e)<<18|(63&t[r++])<<12|(63&t[r++])<<6|63&t[r++])-65536,n+=String.fromCharCode(55296|e>>10,56320|1023&e)):n+=String.fromCharCode(1&i?(31&e)<<6|63&t[r++]:(15&e)<<12|(63&t[r++])<<6|63&t[r++]):n+=String.fromCharCode(e)}},_t=function(){function t(t){this.ondata=t,Xt?this.t=new TextDecoder:this.p=N}return t.prototype.push=function(t,r){if(this.ondata||I(5),r=!!r,this.t)return this.ondata(this.t.decode(t,{stream:!0}),r),void(r&&(this.t.decode().length&&I(8),this.t=null));this.p||I(4);var e=new n(this.p.length+t.length);e.set(this.p),e.set(t,this.p.length);var i=$t(e),o=i.s,s=i.r;r?(s.length&&I(8),this.p=null):this.p=s,this.ondata(o,r)},t}();_e.DecodeUTF8=_t;var tn=function(){function t(t){this.ondata=t}return t.prototype.push=function(t,n){this.ondata||I(5),this.d&&I(4),this.ondata(nn(t),this.d=n||!1)},t}();function nn(t,r){if(r){for(var e=new n(t.length),i=0;i<t.length;++i)e[i]=t.charCodeAt(i);return e}if(Vt)return Vt.encode(t);var o=t.length,s=new n(t.length+(t.length>>1)),a=0,u=function(t){s[a++]=t};for(i=0;i<o;++i){if(a+5>s.length){var h=new n(a+8+(o-i<<1));h.set(s),s=h}var f=t.charCodeAt(i);f<128||r?u(f):f<2048?(u(192|f>>6),u(128|63&f)):f>55295&&f<57344?(u(240|(f=65536+(1047552&f)|1023&t.charCodeAt(++i))>>18),u(128|f>>12&63),u(128|f>>6&63),u(128|63&f)):(u(224|f>>12),u(128|f>>6&63),u(128|63&f))}return D(s,0,a)}function rn(t,n){if(n){for(var r="",e=0;e<t.length;e+=16384)r+=String.fromCharCode.apply(null,t.subarray(e,e+16384));return r}if(Wt)return Wt.decode(t);var i=$t(t),o=i.s;return(r=i.r).length&&I(8),o}_e.EncodeUTF8=tn,_e.strToU8=nn,_e.strFromU8=rn;var en=function(t){return 1==t?3:t<6?2:9==t?1:0},on=function(t,n){return n+30+ht(t,n+26)+ht(t,n+28)},sn=function(t,n,r){var e=ht(t,n+28),i=rn(t.subarray(n+46,n+46+e),!(2048&ht(t,n+8))),o=n+46+e,s=ft(t,n+20),a=r&&4294967295==s?an(t,o):[s,ft(t,n+24),ft(t,n+42)],u=a[0],h=a[1],f=a[2];return[ht(t,n+10),u,h,i,o+ht(t,n+30)+ht(t,n+32),f]},an=function(t,n){for(;1!=ht(t,n);n+=4+ht(t,n+2));return[lt(t,n+12),lt(t,n+4),lt(t,n+20)]},un=function(t){var n=0;if(t)for(var r in t){var e=t[r].length;e>65535&&I(9),n+=e+4}return n},hn=function(t,n,r,e,i,o,s,a){var u=e.length,h=r.extra,f=a&&a.length,l=un(h);ct(t,n,null!=s?33639248:67324752),n+=4,null!=s&&(t[n++]=20,t[n++]=r.os),t[n]=20,n+=2,t[n++]=r.flag<<1|(o<0&&8),t[n++]=i&&8,t[n++]=255&r.compression,t[n++]=r.compression>>8;var c=new Date(null==r.mtime?Date.now():r.mtime),p=c.getFullYear()-1980;if((p<0||p>119)&&I(10),ct(t,n,p<<25|c.getMonth()+1<<21|c.getDate()<<16|c.getHours()<<11|c.getMinutes()<<5|c.getSeconds()>>1),n+=4,-1!=o&&(ct(t,n,r.crc),ct(t,n+4,o<0?-o-2:o),ct(t,n+8,r.size)),ct(t,n+12,u),ct(t,n+14,l),n+=16,null!=s&&(ct(t,n,f),ct(t,n+6,r.attrs),ct(t,n+10,s),n+=14),t.set(e,n),n+=u,l)for(var v in h){var d=h[v],g=d.length;ct(t,n,+v),ct(t,n+2,g),t.set(d,n+4),n+=4+g}return f&&(t.set(a,n),n+=f),n},fn=function(t,n,r,e,i){ct(t,n,101010256),ct(t,n+8,r),ct(t,n+10,r),ct(t,n+12,e),ct(t,n+16,i)},ln=function(){function t(t){this.filename=t,this.c=Y(),this.size=0,this.compression=0}return t.prototype.process=function(t,n){this.ondata(null,t,n)},t.prototype.push=function(t,n){this.ondata||I(5),this.c.p(t),this.size+=t.length,n&&(this.crc=this.c.d()),this.process(t,n||!1)},t}();_e.ZipPassThrough=ln;var cn=function(){function t(t,n){var r=this;n||(n={}),ln.call(this,t),this.d=new wt(n,(function(t,n){r.ondata(null,t,n)})),this.compression=8,this.flag=en(n.level)}return t.prototype.process=function(t,n){try{this.d.push(t,n)}catch(t){this.ondata(t,null,n)}},t.prototype.push=function(t,n){ln.prototype.push.call(this,t,n)},t}();_e.ZipDeflate=cn;var pn=function(){function t(t,n){var r=this;n||(n={}),ln.call(this,t),this.d=new xt(n,(function(t,n,e){r.ondata(t,n,e)})),this.compression=8,this.flag=en(n.level),this.terminate=this.d.terminate}return t.prototype.process=function(t,n){this.d.push(t,n)},t.prototype.push=function(t,n){ln.prototype.push.call(this,t,n)},t}();_e.AsyncZipDeflate=pn;var vn=function(){function t(t){this.ondata=t,this.u=[],this.d=1}return t.prototype.add=function(t){var r=this;if(this.ondata||I(5),2&this.d)this.ondata(I(4+8*(1&this.d),0,1),null,!1);else{var e=nn(t.filename),i=e.length,o=t.comment,s=o&&nn(o),a=i!=t.filename.length||s&&o.length!=s.length,u=i+un(t.extra)+30;i>65535&&this.ondata(I(11,0,1),null,!1);var h=new n(u);hn(h,0,t,e,a,-1);var f=[h],l=function(){for(var t=0,n=f;t<n.length;t++)r.ondata(null,n[t],!1);f=[]},c=this.d;this.d=0;var p=this.u.length,v=Q(t,{f:e,u:a,o:s,t:function(){t.terminate&&t.terminate()},r:function(){if(l(),c){var t=r.u[p+1];t?t.r():r.d=1}c=1}}),d=0;t.ondata=function(e,i,o){if(e)r.ondata(e,i,o),r.terminate();else if(d+=i.length,f.push(i),o){var s=new n(16);ct(s,0,134695760),ct(s,4,t.crc),ct(s,8,d),ct(s,12,t.size),f.push(s),v.c=d,v.b=u+d+16,v.crc=t.crc,v.size=t.size,c&&v.r(),c=1}else c&&l()},this.u.push(v)}},t.prototype.end=function(){var t=this;2&this.d?this.ondata(I(4+8*(1&this.d),0,1),null,!0):(this.d?this.e():this.u.push({r:function(){1&t.d&&(t.u.splice(-1,1),t.e())},t:function(){}}),this.d=3)},t.prototype.e=function(){for(var t=0,r=0,e=0,i=0,o=this.u;i<o.length;i++)e+=46+(h=o[i]).f.length+un(h.extra)+(h.o?h.o.length:0);for(var s=new n(e+22),a=0,u=this.u;a<u.length;a++){var h;hn(s,t,h=u[a],h.f,h.u,-h.c-2,r,h.o),t+=46+h.f.length+un(h.extra)+(h.o?h.o.length:0),r+=h.b}fn(s,t,this.u.length,e,r),this.ondata(null,s,!0),this.d=2},t.prototype.terminate=function(){for(var t=0,n=this.u;t<n.length;t++)n[t].t();this.d=2},t}();function dn(t,r,e){e||(e=r,r={}),"function"!=typeof e&&I(7);var i={};Rt(t,"",i,r);var o=Object.keys(i),s=o.length,a=0,u=0,h=s,f=Array(s),l=[],c=function(){for(var t=0;t<l.length;++t)l[t]()},p=function(t,n){xn((function(){e(t,n)}))};xn((function(){p=e}));var v=function(){var t=new n(u+22),r=a,e=u-a;u=0;for(var i=0;i<h;++i){var o=f[i];try{var s=o.c.length;hn(t,u,o,o.f,o.u,s);var l=30+o.f.length+un(o.extra),c=u+l;t.set(o.c,c),hn(t,a,o,o.f,o.u,s,u,o.m),a+=16+l+(o.m?o.m.length:0),u=c+s}catch(t){return p(t,null)}}fn(t,a,f.length,e,r),p(null,t)};s||v();for(var d=function(t){var n=o[t],r=i[n],e=r[0],h=r[1],d=Y(),g=e.length;d.p(e);var y=nn(n),m=y.length,b=h.comment,w=b&&nn(b),x=w&&w.length,z=un(h.extra),k=0==h.level?0:8,M=function(r,e){if(r)c(),p(r,null);else{var i=e.length;f[t]=Q(h,{size:g,crc:d.d(),c:e,f:y,m:w,u:m!=n.length||w&&b.length!=x,compression:k}),a+=30+m+z+i,u+=76+2*(m+z)+(x||0)+i,--s||v()}};if(m>65535&&M(I(11,0,1),null),k)if(g<16e4)try{M(null,kt(e,h))}catch(t){M(t,null)}else l.push(zt(e,h,M));else M(null,e)},g=0;g<h;++g)d(g);return c}function gn(t,r){r||(r={});var e={},i=[];Rt(t,"",e,r);var o=0,s=0;for(var a in e){var u=e[a],h=u[0],f=u[1],l=0==f.level?0:8,c=(M=nn(a)).length,p=f.comment,v=p&&nn(p),d=v&&v.length,g=un(f.extra);c>65535&&I(11);var y=l?kt(h,f):h,m=y.length,b=Y();b.p(h),i.push(Q(f,{size:h.length,crc:b.d(),c:y,f:M,m:v,u:c!=a.length||v&&p.length!=d,o:o,compression:l})),o+=30+c+g+m,s+=76+2*(c+g)+(d||0)+m}for(var w=new n(s+22),x=o,z=s-o,k=0;k<i.length;++k){var M;hn(w,(M=i[k]).o,M,M.f,M.u,M.c.length);var S=30+M.f.length+un(M.extra);w.set(M.c,M.o+S),hn(w,o,M,M.f,M.u,M.c.length,M.o,M.m),o+=16+S+(M.m?M.m.length:0)}return fn(w,o,i.length,z,x),w}_e.Zip=vn,_e.zip=dn,_e.zipSync=gn;var yn=function(){function t(){}return t.prototype.push=function(t,n){this.ondata(null,t,n)},t.compression=0,t}();_e.UnzipPassThrough=yn;var mn=function(){function t(){var t=this;this.i=new Mt((function(n,r){t.ondata(null,n,r)}))}return t.prototype.push=function(t,n){try{this.i.push(t,n)}catch(t){this.ondata(t,null,n)}},t.compression=8,t}();_e.UnzipInflate=mn;var bn=function(){function t(t,n){var r=this;n<32e4?this.i=new Mt((function(t,n){r.ondata(null,t,n)})):(this.i=new St((function(t,n,e){r.ondata(t,n,e)})),this.terminate=this.i.terminate)}return t.prototype.push=function(t,n){this.i.terminate&&(t=D(t,0)),this.i.push(t,n)},t.compression=8,t}();_e.AsyncUnzipInflate=bn;var wn=function(){function t(t){this.onfile=t,this.k=[],this.o={0:yn},this.p=N}return t.prototype.push=function(t,r){var e=this;if(this.onfile||I(5),this.p||I(4),this.c>0){var i=Math.min(this.c,t.length),o=t.subarray(0,i);if(this.c-=i,this.d?this.d.push(o,!this.c):this.k[0].push(o),(t=t.subarray(i)).length)return this.push(t,r)}else{var s=0,a=0,u=void 0,h=void 0;this.p.length?t.length?((h=new n(this.p.length+t.length)).set(this.p),h.set(t,this.p.length)):h=this.p:h=t;for(var f=h.length,l=this.c,c=l&&this.d,p=function(){var t,n=ft(h,a);if(67324752==n){s=1,u=a,v.d=null,v.c=0;var r=ht(h,a+6),i=ht(h,a+8),o=2048&r,c=8&r,p=ht(h,a+26),d=ht(h,a+28);if(f>a+30+p+d){var g=[];v.k.unshift(g),s=2;var y,m=ft(h,a+18),b=ft(h,a+22),w=rn(h.subarray(a+30,a+=30+p),!o);4294967295==m?(t=c?[-2]:an(h,a),m=t[0],b=t[1]):c&&(m=-1),a+=d,v.c=m;var x={name:w,compression:i,start:function(){if(x.ondata||I(5),m){var t=e.o[i];t||x.ondata(I(14,"unknown compression type "+i,1),null,!1),(y=m<0?new t(w):new t(w,m,b)).ondata=function(t,n,r){x.ondata(t,n,r)};for(var n=0,r=g;n<r.length;n++)y.push(r[n],!1);e.k[0]==g&&e.c?e.d=y:y.push(N,!0)}else x.ondata(null,N,!0)},terminate:function(){y&&y.terminate&&y.terminate()}};m>=0&&(x.size=m,x.originalSize=b),v.onfile(x)}return"break"}if(l){if(134695760==n)return u=a+=12+(-2==l&&8),s=3,v.c=0,"break";if(33639248==n)return u=a-=4,s=3,v.c=0,"break"}},v=this;a<f-4&&"break"!==p();++a);if(this.p=N,l<0){var d=h.subarray(0,s?u-12-(-2==l&&8)-(134695760==ft(h,u-16)&&4):a);c?c.push(d,!!s):this.k[+(2==s)].push(d)}if(2&s)return this.push(h.subarray(a),r);this.p=h.subarray(a)}r&&(this.c&&I(13),this.p=null)},t.prototype.register=function(t){this.o[t.compression]=t},t}();_e.Unzip=wn;var xn="function"==typeof queueMicrotask?queueMicrotask:"function"==typeof setTimeout?setTimeout:function(t){t()};function zn(t,r,e){e||(e=r,r={}),"function"!=typeof e&&I(7);var i=[],o=function(){for(var t=0;t<i.length;++t)i[t]()},s={},a=function(t,n){xn((function(){e(t,n)}))};xn((function(){a=e}));for(var u=t.length-22;101010256!=ft(t,u);--u)if(!u||t.length-u>65558)return a(I(13,0,1),null),o;var h=ht(t,u+8);if(h){var f=h,l=ft(t,u+16),c=4294967295==l||65535==f;if(c){var p=ft(t,u-12);(c=101075792==ft(t,p))&&(f=h=ft(t,p+32),l=ft(t,p+48))}for(var v=r&&r.filter,d=function(r){var e=sn(t,l,c),u=e[0],f=e[1],p=e[2],d=e[3],g=e[4],y=on(t,e[5]);l=g;var m=function(t,n){t?(o(),a(t,null)):(n&&(s[d]=n),--h||a(null,s))};if(!v||v({name:d,size:f,originalSize:p,compression:u}))if(u)if(8==u){var b=t.subarray(y,y+f);if(p<524288||f>.8*p)try{m(null,Tt(b,{out:new n(p)}))}catch(t){m(t,null)}else i.push(At(b,{size:p},m))}else m(I(14,"unknown compression type "+u,1),null);else m(null,D(t,y,y+f));else m(null,null)},g=0;g<f;++g)d()}else a(null,{});return o}function kn(t,r){for(var e={},i=t.length-22;101010256!=ft(t,i);--i)(!i||t.length-i>65558)&&I(13);var o=ht(t,i+8);if(!o)return{};var s=ft(t,i+16),a=4294967295==s||65535==o;if(a){var u=ft(t,i-12);(a=101075792==ft(t,u))&&(o=ft(t,u+32),s=ft(t,u+48))}for(var h=r&&r.filter,f=0;f<o;++f){var l=sn(t,s,a),c=l[0],p=l[1],v=l[2],d=l[3],g=l[4],y=on(t,l[5]);s=g,h&&!h({name:d,size:p,originalSize:v,compression:c})||(c?8==c?e[d]=Tt(t.subarray(y,y+p),{out:new n(v)}):I(14,"unknown compression type "+c):e[d]=D(t,y,y+p))}return e}_e.unzip=zn,_e.unzipSync=kn;return _e});
"""


# ──────────────────────────────────────────────────────────────────────
# Famly GraphQL client
# ──────────────────────────────────────────────────────────────────────

class FamlyClient:
    """Minimal GraphQL client for Famly's API (no external dependencies)."""

    def __init__(self, token, installation_id, platform="docker"):
        self.headers = {
            "x-famly-accesstoken": token,
            "x-famly-installationid": installation_id,
            "x-famly-platform": platform,
            "content-type": "application/json",
            "accept": "*/*",
        }

    def query(self, query_string, variables=None):
        """Run a GraphQL query and return the parsed JSON response."""
        body = json.dumps({"query": query_string, "variables": variables or {}}).encode("utf-8")
        req = urllib.request.Request(GRAPHQL_URL, data=body, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(err_body)
            except Exception:
                raise RuntimeError(f"HTTP {e.code} from Famly: {err_body[:500]}")

    def whoami(self):
        """Check auth — returns the logged-in user's name, or None if not authorized."""
        result = self.query("{ me { me { id email name { fullName } } } }")
        if result.get("errors"):
            return None
        try:
            return result["data"]["me"]["me"]["name"]["fullName"]
        except (KeyError, TypeError):
            return None

    def fetch_observations(self, child_id):
        """Page through all observations for a child. Returns a list of observation dicts."""
        # Use proper GraphQL variables with Famly's custom scalar types.
        # (childIds is [ChildId!]! and after is ObservationCursor — NOT String.)
        query = """
        query($childIds: [ChildId!]!, $first: Int!, $after: ObservationCursor) {
          childDevelopment {
            observations(first: $first, childIds: $childIds, ordering: DATE_DESCENDING, after: $after) {
              results {
                id
                remark { date body richTextBody }
                images { id url width height }
                files { id url name }
                videos {
                  __typename
                  ... on TranscodedVideo { id videoUrl thumbnailUrl duration width height }
                  ... on TranscodingVideo { id }
                }
                createdBy { name { fullName } }
                status { state createdAt }
              }
              next
            }
          }
        }
        """
        all_obs = []
        after = None
        for page in range(MAX_PAGES):
            result = self.query(query, {"childIds": [child_id], "first": PAGE_SIZE, "after": after})
            if result.get("errors"):
                raise RuntimeError(f"GraphQL error: {result['errors'][0].get('message', result['errors'])}")
            obs_data = result["data"]["childDevelopment"]["observations"]
            batch = obs_data["results"]
            all_obs.extend(batch)
            after = obs_data.get("next")
            print(f"  Page {page + 1}: got {len(batch)} observations (total so far: {len(all_obs)})")
            if not after:
                break
        return all_obs


# ──────────────────────────────────────────────────────────────────────
# Download helpers
# ──────────────────────────────────────────────────────────────────────

def safe_filename(name):
    """Make a string safe for use as a filename."""
    keep = "._-"
    return "".join(c if c.isalnum() or c in keep else "_" for c in name).strip("_") or "file"


def local_media_path(obs, kind, index, media_id, output_dir):
    """Compute the local download path for a media item.

    Mirrors the naming in build_download_list so the gallery links resolve
    to the actual files on disk. Returns a path relative to output_dir
    (so the gallery is portable if you move the whole folder).
    """
    date = obs.get("remark", {}).get("date") or "unknown-date"
    obs_short = obs["id"][:8]
    year = date[:4] if date != "unknown-date" else "unknown"
    month = date[5:7] if date != "unknown-date" else "00"
    if kind == "image":
        fname = f"{date}_{obs_short}_img{index:02d}_{media_id[:8]}.jpg"
    elif kind == "video":
        fname = f"{date}_{obs_short}_vid{index:02d}_{media_id[:8]}.mp4"
    else:  # file
        fname = f"{date}_{obs_short}_file{index:02d}_{safe_filename(media_id)}"
    return os.path.join(year, month, fname)


def download_file(url, dest):
    """Download a single file using curl (retries built in). Returns (dest, size, error)."""
    try:
        result = subprocess.run(
            ["curl", "-sS", "-L", "--retry", "3", "--retry-delay", "1", "-o", dest, url],
            capture_output=True, timeout=180,
        )
        size = os.path.getsize(dest) if os.path.exists(dest) else 0
        if size > 100:
            return (dest, size, None)
        return (dest, 0, result.stderr.decode("utf-8", errors="replace")[:200] or "empty file")
    except subprocess.TimeoutExpired:
        return (dest, 0, "timeout")
    except Exception as e:
        return (dest, 0, str(e)[:200])


# MIME types for embedded media (data URIs need the right content-type)
_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".mp4": "video/mp4", ".pdf": "application/pdf"}


def file_to_data_uri(path):
    """Read a file and return a data: URI with the content base64-embedded."""
    ext = os.path.splitext(path)[1].lower()
    mime = _MIME.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_download_list(manifest, output_dir):
    """Turn the observation manifest into a list of (url, dest) downloads."""
    downloads = []
    for obs in manifest:
        for i, img in enumerate(obs["images"], 1):
            rel = local_media_path(obs, "image", i, img["id"], output_dir)
            downloads.append((img["url"], os.path.join(output_dir, rel)))

        for i, vid in enumerate(obs["videos"], 1):
            if not vid.get("videoUrl"):
                continue  # TranscodingVideo (still processing) — skip
            rel = local_media_path(obs, "video", i, vid["id"], output_dir)
            downloads.append((vid["videoUrl"], os.path.join(output_dir, rel)))

        for i, f in enumerate(obs["files"], 1):
            rel = local_media_path(obs, "file", i, f["name"], output_dir)
            downloads.append((f["url"], os.path.join(output_dir, rel)))

    return downloads


def save_observation_sidecars(manifest, output_dir):
    """Save a JSON sidecar per observation with its text + metadata."""
    saved = 0
    for obs in manifest:
        date = obs.get("remark", {}).get("date") or "unknown-date"
        obs_short = obs["id"][:8]
        year = date[:4] if date != "unknown-date" else "unknown"
        month = date[5:7] if date != "unknown-date" else "00"
        folder = os.path.join(output_dir, year, month)
        os.makedirs(folder, exist_ok=True)
        sidecar = {
            "observationId": obs["id"],
            "date": obs.get("remark", {}).get("date"),
            "body": obs.get("remark", {}).get("body"),
            "richTextBody": obs.get("remark", {}).get("richTextBody"),
            "createdBy": obs.get("createdBy", {}).get("name", {}).get("fullName"),
            "status": obs.get("status", {}).get("state"),
            "createdAt": obs.get("status", {}).get("createdAt"),
            "mediaCount": len(obs["images"]) + len(obs["videos"]) + len(obs["files"]),
        }
        path = os.path.join(folder, f"{date}_{obs_short}_observation.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2, ensure_ascii=False)
        saved += 1
    return saved


# ──────────────────────────────────────────────────────────────────────
# Gallery HTML builder
# ──────────────────────────────────────────────────────────────────────

MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}


def fmt_date(d):
    if not d or d == "unknown-date":
        return "Unknown date"
    try:
        y, m, day = d.split("-")
        return f"{MONTH_NAMES.get(m, m)} {int(day)}, {y}"
    except Exception:
        return d


def fmt_duration(s):
    if not s:
        return ""
    m, sec = divmod(int(s), 60)
    return f"{m}:{sec:02d}"


def build_gallery(manifest, output_dir, child_name="", embed=False, embed_videos=True):
    """Build index.html — a beautiful browsable gallery of all media."""
    # Sort by date descending
    sorted_obs = sorted(manifest, key=lambda o: o.get("remark", {}).get("date") or "", reverse=True)

    # Group into year/month sections
    sections = []
    current_key = None
    current_entries = []
    for obs in sorted_obs:
        date = obs.get("remark", {}).get("date") or "unknown-date"
        year = date[:4] if date != "unknown-date" else "unknown"
        month = date[5:7] if date != "unknown-date" else "00"
        key = (year, month)
        if key != current_key:
            if current_entries:
                sections.append((current_key, current_entries))
            current_key = key
            current_entries = [obs]
        else:
            current_entries.append(obs)
    if current_entries:
        sections.append((current_key, current_entries))

    # In embed mode, this dict collects {archive_path: data_uri} for the ZIP button
    _zip_files = {} if embed else None

    def esc(t):
        return html.escape(t or "", quote=True)

    # Build nav + sections HTML
    nav_parts = []
    cards_parts = []
    for (year, month), entries in sections:
        mname = MONTH_NAMES.get(month, month)
        section_id = f"{year}-{month}"
        total_media = sum(len(o["images"]) + len(o["videos"]) + len(o["files"]) for o in entries)
        if total_media == 0:
            continue  # skip empty months (observations with no media)
        nav_parts.append(
            f'<a href="#{section_id}" class="nav-month">{mname} '
            f'<span class="nav-year">{year}</span> '
            f'<span class="nav-count">{total_media}</span></a>'
        )
        cards_parts.append(
            f'<section class="month-section" id="{section_id}">'
            f'<div class="month-header"><h2 class="month-title">{mname} '
            f'<span class="year">{year}</span></h2>'
            f'<span class="month-count">{total_media} {"item" if total_media == 1 else "items"}</span></div>'
            f'<div class="cards-grid">'
        )
        for obs in entries:
            date = obs.get("remark", {}).get("date") or "unknown-date"
            date_display = fmt_date(date)
            n_items = len(obs["images"]) + len(obs["videos"]) + len(obs["files"])
            tiles = []
            for i, img in enumerate(obs["images"], 1):
                local = local_media_path(obs, "image", i, img["id"], output_dir)
                src = file_to_data_uri(os.path.join(output_dir, local)) if embed else local
                if embed:
                    _zip_files[local] = src
                tiles.append(
                    f'<div class="tile" data-type="image" data-src="{esc(src)}">'
                    f'<img src="{esc(src)}" alt="Photo from {esc(date_display)}" loading="lazy"/>'
                    f'<div class="tile-zoom">🔍</div></div>'
                )
            for i, vid in enumerate(obs["videos"], 1):
                if not vid.get("videoUrl"):
                    continue
                local = local_media_path(obs, "video", i, vid["id"], output_dir)
                dur = fmt_duration(vid.get("duration"))
                dur_html = f'<span class="tile-duration">{dur}</span>' if dur else ""
                if embed and not embed_videos:
                    # Skip embedding the video; show a placeholder note
                    tiles.append(
                        f'<div class="tile tile-video-skip">'
                        f'<div class="file-icon">🎬</div>'
                        f'<div class="file-name">Video ({dur or "—"})</div>'
                        f'<div class="file-open">In full archive folder</div></div>'
                    )
                    continue
                src = file_to_data_uri(os.path.join(output_dir, local)) if embed else local
                if embed:
                    _zip_files[local] = src
                tiles.append(
                    f'<div class="tile" data-type="video" data-src="{esc(src)}">'
                    f'<video preload="metadata" muted playsinline><source src="{esc(src)}" type="video/mp4"/></video>'
                    f'<div class="tile-play">▶</div>'
                    f'{dur_html}</div>'
                )
            for i, f in enumerate(obs["files"], 1):
                local = local_media_path(obs, "file", i, f["name"], output_dir)
                src = file_to_data_uri(os.path.join(output_dir, local)) if embed else local
                if embed:
                    _zip_files[local] = src
                tiles.append(
                    f'<a class="tile tile-file" href="{esc(src)}" target="_blank" rel="noopener">'
                    f'<div class="file-icon">📄</div><div class="file-name">{esc(f["name"])}</div>'
                    f'<div class="file-open">Open file ↗</div></a>'
                )
            body = obs.get("remark", {}).get("body")
            body_html = f'<div class="obs-body">{esc(body)}</div>' if body else ""
            author = obs.get("createdBy", {}).get("name", {}).get("fullName")
            author_html = f'<div class="obs-author">✨ by {esc(author)}</div>' if author else ""
            count_label = "photo" if n_items == 1 else "photos"
            cards_parts.append(
                f'<article class="obs-card">'
                f'<div class="obs-date-bar"><span class="obs-date">🗓 {esc(date_display)}</span>'
                f'<span class="obs-count">{n_items} {count_label}</span></div>'
                f'{body_html}<div class="tiles-grid">{"".join(tiles)}</div>{author_html}</article>'
            )
        cards_parts.append("</div></section>")

    nav_html = "\n".join(nav_parts)
    cards_html = "\n".join(cards_parts)

    total_photos = sum(len(o["images"]) for o in manifest)
    total_videos = sum(len(o["videos"]) for o in manifest)
    total_files = sum(len(o["files"]) for o in manifest)
    years_span = sorted(set((o.get("remark", {}).get("date") or "unknown")[:4] for o in manifest))
    title = f"{child_name}'s Learning Journey" if child_name else "Learning Journey"

    # Embed mode: build the download button and the file manifest for the ZIP worker
    if embed and _zip_files:
        zip_manifest_json = json.dumps(_zip_files, ensure_ascii=False)
        embed_button = (
            '\n  <button class="dl-zip-btn" id="dlZip">📥 Download all as ZIP</button>'
            '\n  <div class="dl-zip-status" id="dlStatus"></div>'
            '\n  <div class="dl-zip-progress" id="dlProgress" style="display:none">'
            '<div class="dl-zip-progress-bar" id="dlProgressBar"></div></div>'
        )
        # The ZIP worker script: inlines fflate, receives the file manifest, zips, returns blob
        zip_worker_js = f"""{FFLATE_JS}
self.onmessage=function(e){{
  var files=e.data;
  var total=Object.keys(files).length;
  var zipped={{}};
  var done=0;
  for(var path in files){{
    // decode data URI -> Uint8Array
    var b64=files[path].split(',')[1];
    var bin=atob(b64);
    var u8=new Uint8Array(bin.length);
    for(var j=0;j<bin.length;j++)u8[j]=bin.charCodeAt(j);
    zipped[path]=u8;
    done++;
    if(done%10===0||done===total)self.postMessage({{type:'progress',done:done,total:total}});
  }}
  self.postMessage({{type:'zipping'}});
  var zipResult=fflate.zipSync(zipped,{{level:1}});
  var ab=zipResult.buffer;
  self.postMessage({{type:'done',buffer:ab}},[ab]);
}};"""
        # Create a Blob URL for the worker script
        worker_blob = "data:text/javascript;base64," + base64.b64encode(zip_worker_js.encode("utf-8")).decode("ascii")
        zip_download_script = f"""
<script id="zipManifest" type="application/json">{zip_manifest_json}</script>
<script>
(function(){{
  var btn=document.getElementById('dlZip');
  var status=document.getElementById('dlStatus');
  var prog=document.getElementById('dlProgress');
  var progBar=document.getElementById('dlProgressBar');
  if(!btn)return;
  btn.onclick=function(){{
    btn.disabled=true;
    status.textContent='Preparing files...';
    prog.style.display='block';
    progBar.style.width='0%';
    var manifest=JSON.parse(document.getElementById('zipManifest').textContent);
    var worker=new Worker({worker_blob!r});
    worker.onmessage=function(e){{
      var d=e.data;
      if(d.type==='progress'){{
        var pct=Math.round(d.done/d.total*80);
        status.textContent='Reading '+d.done+'/'+d.total+' files...';
        progBar.style.width=pct+'%';
      }}else if(d.type==='zipping'){{
        status.textContent='Compressing ZIP...';
        progBar.style.width='90%';
      }}else if(d.type==='done'){{
        progBar.style.width='100%';
        status.textContent='Saving...';
        var blob=new Blob([d.buffer],{{type:'application/zip'}});
        var url=URL.createObjectURL(blob);
        var a=document.createElement('a');
        a.href=url;
        a.download={child_name!r}?{child_name!r}+'-famly-archive.zip':'famly-archive.zip';
        document.body.appendChild(a);a.click();document.body.removeChild(a);
        setTimeout(function(){{URL.revokeObjectURL(url);}},5000);
        status.textContent='Done! ✓';
        btn.disabled=false;
        worker.terminate();
      }}
    }};
    worker.onerror=function(err){{
      status.textContent='Error: '+err.message;
      btn.disabled=false;
      prog.style.display='none';
      worker.terminate();
    }};
    worker.postMessage(manifest);
  }};
}})();
</script>"""
    else:
        zip_download_script = ""
        embed_button = ""

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{esc(title)} 🌈</title>
<style>
:root {{
  --pink:#FF6B9D;--coral:#FF8E72;--yellow:#FFD93D;--mint:#6BCB77;
  --sky:#4D96FF;--purple:#B983FF;--cream:#FFF8F0;--paper:#FFFDF7;
  --ink:#2D2A32;--soft:#6B6573;--line:#EFE6DC;
  --shadow:0 8px 30px rgba(180,150,130,0.18);
  --shadow-hover:0 16px 50px rgba(180,150,130,0.30);
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",sans-serif;
  background:var(--paper);
  background-image:
    radial-gradient(circle at 12% 18%,rgba(255,107,157,0.08) 0,transparent 40%),
    radial-gradient(circle at 88% 82%,rgba(109,150,255,0.08) 0,transparent 40%),
    radial-gradient(circle at 50% 50%,rgba(255,217,61,0.05) 0,transparent 60%);
  color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased;
}}
.hero{{
  position:relative;text-align:center;padding:80px 24px 56px;overflow:hidden;
  background:linear-gradient(135deg,#FFF6E5 0%,#FFE8F0 50%,#E8F4FF 100%);
  border-bottom:1px solid var(--line);
}}
.hero::before{{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:
    radial-gradient(circle at 20% 30%,rgba(255,107,157,0.15) 0,transparent 25%),
    radial-gradient(circle at 80% 20%,rgba(185,131,255,0.15) 0,transparent 25%),
    radial-gradient(circle at 50% 80%,rgba(255,217,61,0.15) 0,transparent 25%);
}}
.hero-inner{{position:relative;z-index:1;max-width:900px;margin:0 auto;}}
.hero-emoji{{font-size:56px;letter-spacing:12px;margin-bottom:18px;animation:float 4s ease-in-out infinite;}}
@keyframes float{{0%,100%{{transform:translateY(0);}}50%{{transform:translateY(-8px);}}}}
.hero h1{{font-family:"Georgia","Playfair Display",serif;font-size:clamp(34px,6vw,56px);
  font-weight:700;color:var(--ink);letter-spacing:-0.02em;margin-bottom:14px;line-height:1.1;}}
.hero h1 .heart{{color:var(--pink);display:inline-block;animation:beat 1.6s ease-in-out infinite;}}
@keyframes beat{{0%,100%{{transform:scale(1);}}15%{{transform:scale(1.18);}}30%{{transform:scale(1);}}45%{{transform:scale(1.12);}}}}
.hero p{{font-size:clamp(15px,2.5vw,19px);color:var(--soft);margin-bottom:32px;font-style:italic;}}
.hero-stats{{display:flex;justify-content:center;gap:clamp(20px,5vw,56px);flex-wrap:wrap;}}
.stat{{text-align:center;}}
.stat-num{{font-family:"Georgia",serif;font-size:clamp(28px,5vw,40px);font-weight:700;color:var(--ink);line-height:1;}}
.stat-num.pink{{color:var(--pink);}}.stat-num.purple{{color:var(--purple);}}
.stat-num.sky{{color:var(--sky);}}.stat-num.mint{{color:var(--mint);}}
.stat-label{{font-size:12px;text-transform:uppercase;letter-spacing:0.12em;color:var(--soft);margin-top:6px;font-weight:600;}}
.timeline{{
  position:sticky;top:0;z-index:50;background:rgba(255,253,247,0.92);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border-bottom:1px solid var(--line);padding:14px 0 14px 24px;
  display:flex;gap:8px;
  overflow-x:auto;overflow-y:hidden;
  scroll-behavior:smooth;
  scrollbar-width:thin;scrollbar-color:var(--line) transparent;
  -webkit-overflow-scrolling:touch;
  /* fade edges so it's clear there's more to scroll */
  mask-image:linear-gradient(to right,transparent 0,black 24px,black calc(100% - 24px),transparent 100%);
  -webkit-mask-image:linear-gradient(to right,transparent 0,black 24px,black calc(100% - 24px),transparent 100%);
}}
.timeline::-webkit-scrollbar{{height:4px;}}
.timeline::-webkit-scrollbar-track{{background:transparent;}}
.timeline::-webkit-scrollbar-thumb{{background:var(--line);border-radius:999px;}}
.timeline::after{{content:"";flex:0 0 24px;}} /* trailing space so last pill isn't clipped by mask */
.nav-month{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
  border-radius:999px;text-decoration:none;font-size:13px;font-weight:600;
  color:var(--soft);background:transparent;border:1px solid transparent;
  transition:all 0.2s;white-space:nowrap;}}
.nav-month:hover{{background:var(--cream);color:var(--ink);border-color:var(--line);}}
.nav-month.active{{background:var(--ink);color:white;border-color:var(--ink);}}
.nav-month.active .nav-count{{background:rgba(255,255,255,0.25);color:white;}}
.nav-month.active .nav-year{{opacity:0.7;}}
.nav-year{{font-size:11px;opacity:0.55;font-weight:500;}}
.nav-count{{font-size:11px;background:var(--cream);padding:2px 7px;border-radius:999px;color:var(--soft);font-weight:500;}}
.month-section{{max-width:1100px;margin:0 auto;padding:56px 24px 16px;}}
.month-header{{display:flex;align-items:baseline;justify-content:space-between;gap:16px;
  margin-bottom:28px;padding-bottom:14px;border-bottom:2px dashed var(--line);}}
.month-title{{font-family:"Georgia",serif;font-size:clamp(26px,4vw,38px);font-weight:700;
  color:var(--ink);letter-spacing:-0.01em;}}
.month-title .year{{font-size:0.55em;color:var(--soft);font-weight:400;margin-left:10px;}}
.month-count{{font-size:13px;color:var(--soft);background:var(--cream);padding:6px 14px;
  border-radius:999px;font-weight:600;white-space:nowrap;}}
.obs-card{{background:white;border-radius:20px;padding:20px;margin-bottom:28px;
  box-shadow:var(--shadow);border:1px solid var(--line);
  transition:transform 0.25s ease,box-shadow 0.25s ease;}}
.obs-card:hover{{transform:translateY(-2px);box-shadow:var(--shadow-hover);}}
.obs-date-bar{{display:flex;justify-content:space-between;align-items:center;
  margin-bottom:14px;flex-wrap:wrap;gap:8px;}}
.obs-date{{font-size:15px;font-weight:700;color:var(--ink);}}
.obs-count{{font-size:12px;color:var(--soft);background:var(--cream);padding:4px 12px;
  border-radius:999px;font-weight:600;}}
.obs-body{{font-size:15px;color:var(--ink);margin-bottom:14px;padding:12px 16px;
  background:linear-gradient(135deg,#FFF9F0,#FFF4FA);border-radius:12px;
  border-left:4px solid var(--pink);white-space:pre-wrap;line-height:1.55;}}
.obs-author{{font-size:12px;color:var(--soft);margin-top:12px;font-style:italic;text-align:right;}}
.tiles-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;}}
.tile{{position:relative;border-radius:14px;overflow:hidden;cursor:zoom-in;
  aspect-ratio:3/4;background:var(--cream);transition:transform 0.2s ease;}}
.tile:hover{{transform:scale(1.02);}}
.tile img,.tile video{{width:100%;height:100%;object-fit:cover;display:block;background:var(--cream);}}
.tile-zoom,.tile-play{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,0.92);
  display:flex;align-items:center;justify-content:center;font-size:20px;
  opacity:0;transition:opacity 0.2s;pointer-events:none;box-shadow:0 4px 14px rgba(0,0,0,0.25);}}
.tile:hover .tile-zoom,.tile:hover .tile-play{{opacity:1;}}
.tile-play{{font-size:16px;padding-left:3px;}}
.tile-duration{{position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.7);
  color:white;font-size:11px;font-weight:600;padding:3px 7px;border-radius:6px;}}
.tile-file{{display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;text-decoration:none;color:var(--ink);padding:16px 12px;
  background:linear-gradient(135deg,#FFF3E0,#FFE0E0);border:2px dashed var(--coral);
  cursor:pointer;aspect-ratio:3/4;}}
.tile-file:hover{{background:linear-gradient(135deg,#FFE8CC,#FFD0D0);transform:scale(1.02);}}
.file-icon{{font-size:36px;margin-bottom:8px;}}
.file-name{{font-size:12px;font-weight:600;word-break:break-word;line-height:1.3;}}
.file-open{{font-size:11px;color:var(--coral);margin-top:8px;font-weight:700;}}
.lightbox{{position:fixed;inset:0;z-index:1000;background:rgba(20,18,24,0.94);
  display:none;align-items:center;justify-content:center;padding:24px;flex-direction:column;gap:16px;}}
.lightbox.open{{display:flex;}}
.lightbox-content{{position:relative;max-width:95vw;max-height:85vh;
  display:flex;align-items:center;justify-content:center;}}
.lightbox-content img,.lightbox-content video{{max-width:95vw;max-height:80vh;
  border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,0.5);object-fit:contain;}}
.lightbox-content video{{background:black;}}
.lightbox-close,.lightbox-nav{{position:absolute;border-radius:50%;
  background:rgba(255,255,255,0.15);border:none;color:white;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:background 0.2s;z-index:1001;}}
.lightbox-close{{top:18px;right:18px;width:44px;height:44px;font-size:24px;}}
.lightbox-nav{{top:50%;transform:translateY(-50%);width:50px;height:50px;font-size:22px;}}
.lightbox-nav:hover,.lightbox-close:hover{{background:rgba(255,255,255,0.3);}}
.lightbox-nav.prev{{left:18px;}}.lightbox-nav.next{{right:18px;}}
.lightbox-caption{{color:rgba(255,255,255,0.8);font-size:13px;text-align:center;max-width:600px;}}
footer{{text-align:center;padding:48px 24px 64px;color:var(--soft);font-size:13px;
  border-top:2px dashed var(--line);margin-top:40px;}}
footer .heart{{color:var(--pink);}}
@media (max-width:600px){{
  .tiles-grid{{grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;}}
  .obs-card{{padding:14px;border-radius:16px;}}
  .month-section{{padding:40px 14px 10px;}}
  .hero{{padding:56px 18px 40px;}}
  .lightbox-nav{{width:40px;height:40px;font-size:18px;}}
  .lightbox-close{{width:38px;height:38px;font-size:20px;top:12px;right:12px;}}
  .obs-date{{font-size:14px;}}
  .obs-count{{font-size:11px;}}
  .nav-month{{font-size:12px;padding:5px 11px;}}
  .timeline{{padding:10px 0 10px 14px;gap:6px;}}
  .month-header{{margin-bottom:20px;padding-bottom:10px;}}
}}
@media (max-width:400px){{
  .tiles-grid{{grid-template-columns:repeat(2,1fr);gap:6px;}}
  .hero-emoji{{font-size:44px;letter-spacing:8px;}}
  .hero-stats{{gap:16px;}}
  .stat-num{{font-size:26px;}}
  .obs-card{{padding:12px;border-radius:14px;}}
  .month-section{{padding:32px 10px 8px;}}
  .tile{{border-radius:10px;}}
}}
/* touch devices: bigger tap targets, no hover-only affordances */
@media (hover:none){{
  .tile-zoom,.tile-play{{opacity:0.85;}}
  .tile:hover{{transform:none;}}
  .obs-card:hover{{transform:none;box-shadow:var(--shadow);}}
}}
/* Download-all-as-ZIP button (embed mode only) */
.dl-zip-btn{{
  margin-top:28px;padding:14px 32px;
  background:linear-gradient(135deg,var(--pink),var(--coral));
  color:white;border:none;border-radius:999px;
  font-size:16px;font-weight:700;cursor:pointer;
  box-shadow:0 8px 24px rgba(255,107,157,0.35);
  transition:transform 0.2s,box-shadow 0.2s;letter-spacing:0.02em;
}}
.dl-zip-btn:hover{{transform:translateY(-2px);box-shadow:0 12px 32px rgba(255,107,157,0.45);}}
.dl-zip-btn:active{{transform:translateY(0);}}
.dl-zip-btn:disabled{{opacity:0.7;cursor:wait;transform:none;}}
.dl-zip-status{{
  margin-top:14px;font-size:14px;color:var(--soft);min-height:20px;
  font-weight:500;
}}
.dl-zip-progress{{
  margin-top:10px;width:100%;max-width:300px;height:6px;
  background:var(--line);border-radius:999px;overflow:hidden;
  margin-left:auto;margin-right:auto;
}}
.dl-zip-progress-bar{{
  height:100%;background:linear-gradient(90deg,var(--pink),var(--coral));
  width:0%;transition:width 0.3s;border-radius:999px;
}}
/* video-skip placeholder tile (embed mode, no videos) */
.tile-video-skip{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;padding:14px 8px;border-radius:14px;
  background:var(--cream);border:2px dashed var(--line);
  opacity:0.75;
}}
</style>
</head>
<body>
<header class="hero"><div class="hero-inner">
  <div class="hero-emoji">🌈⭐🦋🌸</div>
  <h1>{esc(title)} <span class="heart">♥</span></h1>
  <p>A little collection of big moments ✨</p>
  <div class="hero-stats">
    <div class="stat"><div class="stat-num pink">{total_photos}</div><div class="stat-label">Photos</div></div>
    <div class="stat"><div class="stat-num purple">{total_videos}</div><div class="stat-label">Videos</div></div>
    <div class="stat"><div class="stat-num sky">{len(manifest)}</div><div class="stat-label">Observations</div></div>
    <div class="stat"><div class="stat-num mint">{len(years_span)}</div><div class="stat-label">Years</div></div>
  </div>{embed_button}
</div></header>
<nav class="timeline">{nav_html}</nav>
<main>{cards_html}</main>
<footer>Made with <span class="heart">♥</span> &nbsp;·&nbsp; {total_photos + total_videos + total_files} memories kept safe ✨</footer>
<div class="lightbox" id="lightbox">
  <button class="lightbox-close" id="lbClose">✕</button>
  <button class="lightbox-nav prev" id="lbPrev">‹</button>
  <button class="lightbox-nav next" id="lbNext">›</button>
  <div class="lightbox-content" id="lbContent"></div>
  <div class="lightbox-caption" id="lbCaption"></div>
</div>
<script>
(function(){{
  var lb=document.getElementById('lightbox'),lbC=document.getElementById('lbContent'),lbCap=document.getElementById('lbCaption');
  var tiles=[],idx=0;
  function open(t,i){{tiles=t;idx=i;render();lb.classList.add('open');document.body.style.overflow='hidden';}}
  function render(){{
    var t=tiles[idx];if(!t)return;
    lbC.innerHTML=t.type==='image'?'<img src="'+t.src+'"/>':'<video src="'+t.src+'" controls autoplay playsinline></video>';
    lbCap.textContent=(idx+1)+' / '+tiles.length;
  }}
  function close(){{lb.classList.remove('open');lbC.innerHTML='';document.body.style.overflow='';}}
  function next(){{idx=(idx+1)%tiles.length;render();}}
  function prev(){{idx=(idx-1+tiles.length)%tiles.length;render();}}
  document.getElementById('lbClose').onclick=close;
  document.getElementById('lbNext').onclick=next;
  document.getElementById('lbPrev').onclick=prev;
  lb.onclick=function(e){{if(e.target===lb)close();}};
  document.onkeydown=function(e){{
    if(!lb.classList.contains('open'))return;
    if(e.key==='Escape')close();else if(e.key==='ArrowRight')next();else if(e.key==='ArrowLeft')prev();
  }};
  document.querySelectorAll('.obs-card').forEach(function(card){{
    var t=[];card.querySelectorAll('.tile[data-type]').forEach(function(tile,i){{
      t.push({{type:tile.dataset.type,src:tile.dataset.src}});
      tile.onclick=function(){{open(t,i);}};
    }});
  }});

  // Highlight the current month in the nav as you scroll, and auto-scroll
  // the nav strip to keep the active pill visible.
  var timeline=document.querySelector('.timeline');
  var navLinks=Array.prototype.slice.call(timeline.querySelectorAll('.nav-month'));
  var sections=navLinks.map(function(a){{return document.getElementById(a.getAttribute('href').slice(1));}});
  var activeLink=null;
  function updateActive(){{
    var scrollY=window.scrollY+120;
    var current=sections[0];
    for(var i=0;i<sections.length;i++){{
      if(sections[i]&&sections[i].offsetTop<=scrollY) current=sections[i];
    }}
    if(current){{
      var id=current.id;
      var link=navLinks.find(function(a){{return a.getAttribute('href')==='#'+id;}});
      if(link&&link!==activeLink){{
        if(activeLink)activeLink.classList.remove('active');
        link.classList.add('active');
        activeLink=link;
        // scroll the nav strip so the active pill is roughly centered
        var tlLeft=timeline.scrollLeft,tlWidth=timeline.clientWidth;
        var linkLeft=link.offsetLeft,linkWidth=link.offsetWidth;
        var target=linkLeft-(tlWidth-linkWidth)/2;
        timeline.scrollTo({{left:Math.max(0,target),behavior:'smooth'}});
      }}
    }}
  }}
  var ticking=false;
  window.addEventListener('scroll',function(){{
    if(!ticking){{window.requestAnimationFrame(function(){{updateActive();ticking=false;}});ticking=true;}}
  }},{{passive:true}});
  updateActive();
}})();
</script>
{zip_download_script}
</body>
</html>"""

    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return html_path


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download your child's Famly learning journey and build a gallery.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=INSTRUCTIONS,
    )
    parser.add_argument("--token", required=False, help="Your Famly access token (x-famly-accesstoken)")
    parser.add_argument("--installation-id", required=False, help="Your Famly installation ID (x-famly-installationid)")
    parser.add_argument("--child-id", required=False, help="Your child's ID (from the URL)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output folder (default: famly-archive)")
    parser.add_argument("--child-name", default="", help="Child's name for the gallery title (optional)")
    parser.add_argument(
        "--gallery-only",
        action="store_true",
        help="Skip fetching and downloading — just rebuild index.html from the existing "
             "manifest.json in --output-dir. Useful to pick up script/gallery updates without "
             "needing your token, installation ID, or child ID.",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Embed ALL media (photos, videos, PDFs) as base64 data URIs directly inside "
             "index.html, producing a single self-contained file you can email or share — "
             "no folder needed. Also adds a 'Download all as ZIP' button so the recipient "
             "can extract the original files. The HTML will be large (~100+ MB for a full "
             "archive). Combine with --gallery-only to embed from an existing manifest.",
    )
    parser.add_argument(
        "--embed-no-videos",
        action="store_true",
        help="With --embed: skip embedding videos (they're the bulk of the size). Videos "
             "show a placeholder tile instead. Use this to share a lighter HTML file "
             "(~30-40 MB for photos + PDFs only). The full archive folder still has the videos.",
    )
    args = parser.parse_args()

    # Gallery-only mode: load the existing manifest and rebuild the HTML
    if args.gallery_only:
        print()
        print("🎨  Famly Gallery Builder (gallery-only mode)")
        print("─" * 50)
        manifest_path = os.path.join(args.output_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            print(f"\n❌  No manifest.json found in: {os.path.abspath(args.output_dir)}")
            print("       Run the script without --gallery-only first to download everything,")
            print("       then use --gallery-only to refresh the gallery later.")
            sys.exit(1)
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"\n    📂  Loaded {len(manifest)} observations from manifest.json")
        child_name = args.child_name or ""
        if args.embed:
            print("    📦  Embedding media into a single self-contained HTML...")
        html_path = build_gallery(
            manifest, args.output_dir, child_name,
            embed=args.embed, embed_videos=not args.embed_no_videos,
        )
        print(f"    ✅  Gallery rebuilt: {html_path}")
        total_images = sum(len(o["images"]) for o in manifest)
        total_videos = sum(len(o["videos"]) for o in manifest)
        total_files = sum(len(o["files"]) for o in manifest)
        dates = sorted(o.get("remark", {}).get("date") for o in manifest if o.get("remark", {}).get("date"))
        print("\n" + "═" * 50)
        print("🎉  Gallery refreshed!")
        print("═" * 50)
        print(f"  📁  Folder:  {os.path.abspath(args.output_dir)}")
        print(f"  🌐  Gallery: {os.path.abspath(html_path)}")
        print(f"  📷  Photos:  {total_images}")
        print(f"  🎬  Videos:  {total_videos}")
        print(f"  📄  Files:   {total_files}")
        if dates:
            print(f"  🗓   Years:   {dates[0][:4]} → {dates[-1][:4]}")
        print()
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", html_path], check=False)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", html_path], check=False)
            elif sys.platform == "win32":
                subprocess.run(["start", html_path], shell=True, check=False)
        except Exception:
            pass
        print("Your memories are safe. 💛")
        return

    # If any required arg is missing, print instructions and exit
    missing = []
    if not args.token:
        missing.append("--token")
    if not args.installation_id:
        missing.append("--installation-id")
    if not args.child_id:
        missing.append("--child-id")
    if missing:
        print(INSTRUCTIONS)
        print(f"\n{'─'*70}")
        print(f"  Missing required arguments: {', '.join(missing)}")
        print(f"{'─'*70}\n")
        sys.exit(1)

    print()
    print("🌈  Famly Learning Journey Downloader")
    print("─" * 50)

    # 1. Validate auth
    print("\n📡  Connecting to Famly...")
    client = FamlyClient(args.token, args.installation_id)
    who = client.whoami()
    if who:
        print(f"    ✅ Logged in as: {who}")
    else:
        print("    ⚠️  Couldn't confirm your identity (the 'me' query failed).")
        print("       This is sometimes normal for parent accounts — continuing anyway.")
        print("       If you get no results, your token may have expired; get a fresh one.")

    # 2. Fetch observations
    print(f"\n📥  Fetching learning journey for child {args.child_id[:8]}...")
    try:
        manifest = client.fetch_observations(args.child_id)
    except Exception as e:
        print(f"\n❌  Error fetching observations: {e}")
        print("       Check that your CHILD ID is correct and your TOKEN hasn't expired.")
        sys.exit(1)

    if not manifest:
        print("\n⚠️  No observations found for this child.")
        print("       This could mean:")
        print("       • The nursery hasn't added any learning journey entries yet, or")
        print("       • Your TOKEN has expired — get a fresh one (see instructions).")
        print("       • The CHILD ID is wrong — double-check it against the URL.")
        sys.exit(0)

    total_images = sum(len(o["images"]) for o in manifest)
    total_videos = sum(len(o["videos"]) for o in manifest)
    total_files = sum(len(o["files"]) for o in manifest)
    dates = sorted(o.get("remark", {}).get("date") for o in manifest if o.get("remark", {}).get("date"))
    print(f"\n    ✅ Found {len(manifest)} observations:")
    print(f"       📷 {total_images} photos")
    print(f"       🎬 {total_videos} videos")
    print(f"       📄 {total_files} files")
    if dates:
        print(f"       🗓  Date range: {dates[0]} → {dates[-1]}")

    # 3. Save manifest
    os.makedirs(args.output_dir, exist_ok=True)
    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n💾  Saved manifest: {manifest_path}")

    # 4. Save observation sidecars
    print("\n📝  Saving observation details...")
    saved = save_observation_sidecars(manifest, args.output_dir)
    print(f"    ✅ Saved {saved} observation sidecars")

    # 5. Build download list
    downloads = build_download_list(manifest, args.output_dir)
    total_dl = len(downloads)
    print(f"\n⬇️  Downloading {total_dl} files (8 at a time)...")

    # Skip already-downloaded files
    to_do = [(url, dest) for url, dest in downloads if not (os.path.exists(dest) and os.path.getsize(dest) > 100)]
    skipped = total_dl - len(to_do)
    if skipped:
        print(f"    ({skipped} already downloaded — skipping those)")

    # Download in parallel
    ok = fail = 0
    failures = []
    if to_do:
        # Create all needed directories first
        for url, dest in to_do:
            os.makedirs(os.path.dirname(dest), exist_ok=True)

        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as ex:
            futures = {ex.submit(download_file, url, dest): (url, dest) for url, dest in to_do}
            for i, fut in enumerate(as_completed(futures), 1):
                dest, size, err = fut.result()
                if size > 100:
                    ok += 1
                else:
                    fail += 1
                    failures.append((os.path.basename(dest), err))
                if i % 20 == 0 or i == len(to_do):
                    print(f"    Progress: {i}/{len(to_do)}  (✅ {ok}  ❌ {fail})")

    print(f"\n    ✅ Downloaded: {ok}")
    if fail:
        print(f"    ❌ Failed: {fail}")
        for name, err in failures[:10]:
            print(f"       • {name}: {err}")

    # 6. Build gallery
    print("\n🎨  Building gallery...")
    child_name = args.child_name or ""
    if args.embed:
        print("    📦  Embedding media into a single self-contained HTML...")
    html_path = build_gallery(
        manifest, args.output_dir, child_name,
        embed=args.embed, embed_videos=not args.embed_no_videos,
    )
    print(f"    ✅ Gallery: {html_path}")

    # 7. Summary + open
    print("\n" + "═" * 50)
    print("🎉  All done! Here's your archive:")
    print("═" * 50)
    print(f"  📁  Folder:  {os.path.abspath(args.output_dir)}")
    print(f"  🌐  Gallery: {os.path.abspath(html_path)}")
    print(f"  📷  Photos:  {total_images}")
    print(f"  🎬  Videos:  {total_videos}")
    print(f"  📄  Files:   {total_files}")
    if dates:
        print(f"  🗓   Years:   {dates[0][:4]} → {dates[-1][:4]}")
    print()
    print("  Opening the gallery in your browser now... ✨")
    print()

    # Open in default browser
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", html_path], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", html_path], check=False)
        elif sys.platform == "win32":
            subprocess.run(["start", html_path], shell=True, check=False)
    except Exception:
        pass  # not critical

    print("Your memories are safe. 💛")


if __name__ == "__main__":
    main()
