## 前端对接说明（Morphology API）

- **服务域名**: `https://rubg.egg404.com`
- **接口前缀**: `/api/morph`
- **支持语言**: 俄语 `ru`、乌克兰语 `uk`
- **核心能力**:
  - 🔍 **智能分析**: 自动推断词性并展示所有相关词形变化
  - 📝 **词性标注**: 详细的语法特征分析和置信度
  - 📚 **名词变格**: 六格 × 单/复数完整变格表
  - 📝 **形容词变格**: 六格 × 单/复数 × 三性变格表
  - 🏃 **动词变位**: 时态 × 人称 × 数变位表
  - 🌳 **词干词族**: 词干提取和完整词族信息
  - ✏️ **拼写检查**: 拼写校正和相似词建议
  - 🔍 **原形查找**: 获取单词的所有可能原形
  - 📊 **批量分析**: 文本分析和批量处理
  - 🎯 **词形生成**: 根据目标语法特征生成词形
  - ✅ **语法检查**: 检查单词是否符合上下文语法要求
- 形态学引擎: `pymorphy2`（俄/乌词形分析与生成），参考仓库：[pymorphy2/pymorphy2](https://github.com/pymorphy2/pymorphy2)

---

## 一、统一约定
- **Base URL**: `https://rubg.egg404.com`
- **CORS**: 服务器已开启 `CORS`，可直接在浏览器中跨域请求。
- **字符集**: `UTF-8`，请直接传递西里尔文字符，避免对 JSON 里的俄/乌文字再次 URL 编码。
- **常用语法标签（grammemes）示例**:
  - 格：`nomn`(主格) `gent`(属格) `datv`(与格) `accs`(宾格) `ablt`(工具格) `loct`(前置格)
  - 数：`sing`(单数) `plur`(复数)
  - 性：`masc`(阳性) `femn`(阴性) `neut`(中性)

> 说明：不同词类/词典项的可用标签组合并不完全一致，非法组合将返回空结果或 `inflected: null`。

---

## 二、接口定义

### 🔍 1) 智能分析（推荐使用）
- 路径: `GET /api/morph/smart-analysis`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "is_known": true,
  "primary_pos": "NOUN",
  "confidence": 1.0,
  "analysis": {
    "pos_tagging": {
      "pos_tags": [
        {
          "word": "друг",
          "normal_form": "друг",
          "pos": "NOUN",
          "tag": "NOUN,anim,masc sing,nomn",
          "score": 1.0,
          "is_known": true,
          "grammemes": ["NOUN","anim","masc","nomn","sing"],
          "cyr_grammemes": ["anim","m","noun","s","v_naz"],
          "case": "nomn",
          "gender": "masc",
          "number": "sing",
          "person": null,
          "tense": null,
          "aspect": null,
          "voice": null,
          "mood": null,
          "animacy": "anim"
        }
      ],
      "is_known": true
    },
    "comprehensive_changes": {
      "noun_declension": {
        "cells": [
          {"case":"nomn","number":"sing","gender":"masc","form":"друг"},
          {"case":"gent","number":"sing","gender":"masc","form":"друга"}
        ]
      },
      "adjective_declension": {"cells": []},
      "verb_conjugation": {"cells": []}
    },
    "stem_lexeme": {
      "stems": [{"word":"друг","stem":"друг","pos":"NOUN","score":1.0}],
      "lexemes": [{"word":"друг","lexeme_forms":[...],"total_forms":12}]
    },
    "normal_forms": {"normal_forms":["друг"],"count":1},
    "spell_check": {"is_known":true,"suggestions":[]}
  }
}
```

### 📝 2) 词性标注
- 路径: `GET /api/morph/pos-tagging`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "pos_tags": [
    {
      "word": "друг",
      "normal_form": "друг",
      "pos": "NOUN",
      "tag": "NOUN,anim,masc sing,nomn",
      "score": 1.0,
      "is_known": true,
      "grammemes": ["NOUN","anim","masc","nomn","sing"],
      "cyr_grammemes": ["anim","m","noun","s","v_naz"],
      "case": "nomn",
      "gender": "masc",
      "number": "sing",
      "person": null,
      "tense": null,
      "aspect": null,
      "voice": null,
      "mood": null,
      "animacy": "anim"
    }
  ],
  "is_known": true
}
```

### 🌳 3) 词干词族
- 路径: `GET /api/morph/stem-lexeme`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "stems": [
    {
      "word": "друг",
      "stem": "друг",
      "pos": "NOUN",
      "score": 1.0
    }
  ],
  "lexemes": [
    {
      "word": "друг",
      "lexeme_forms": [
        {
          "word": "друг",
          "tag": "NOUN,anim,masc sing,nomn",
          "grammemes": ["NOUN","anim","masc","nomn","sing"]
        },
        {
          "word": "друга",
          "tag": "NOUN,anim,masc sing,gent",
          "grammemes": ["NOUN","anim","gent","masc","sing"]
        }
      ],
      "total_forms": 12
    }
  ]
}
```

### ✏️ 4) 拼写检查
- 路径: `GET /api/morph/spell-check`
- 参数:
  - `word`(string, 必填): 待检查的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друга",
  "language": "ru",
  "is_known": true,
  "suggestions": []
}
```

### 🔍 5) 原形查找
- 路径: `GET /api/morph/normal-forms`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друга",
  "language": "ru",
  "normal_forms": ["друг"],
  "count": 1,
  "error": null
}
```

### 📚 6) 名词变格
- 路径: `GET /api/morph/declension`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "normal_form": "друг",
  "pos": "NOUN",
  "cells": [
    {"case":"nomn","number":"sing","gender":"masc","form":"друг"},
    {"case":"nomn","number":"plur","gender":null,"form":"друзья"},
    {"case":"gent","number":"sing","gender":"masc","form":"друга"},
    {"case":"gent","number":"plur","gender":null,"form":"друзей"},
    {"case":"datv","number":"sing","gender":"masc","form":"другу"},
    {"case":"datv","number":"plur","gender":null,"form":"друзьям"},
    {"case":"accs","number":"sing","gender":"masc","form":"друга"},
    {"case":"accs","number":"plur","gender":null,"form":"друзей"},
    {"case":"ablt","number":"sing","gender":"masc","form":"другом"},
    {"case":"ablt","number":"plur","gender":null,"form":"друзьями"},
    {"case":"loct","number":"sing","gender":"masc","form":"друге"},
    {"case":"loct","number":"plur","gender":null,"form":"друзьях"}
  ]
}
```

### 📝 7) 形容词变格
- 路径: `GET /api/morph/adjective-declension`
- 参数:
  - `word`(string, 必填): 待分析的形容词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "красивый",
  "language": "ru",
  "normal_form": "красивый",
  "pos": "ADJF",
  "cells": [
    {"case":"nomn","number":"sing","gender":"masc","form":"красивый"},
    {"case":"nomn","number":"sing","gender":"femn","form":"красивая"},
    {"case":"nomn","number":"sing","gender":"neut","form":"красивое"},
    {"case":"nomn","number":"plur","gender":null,"form":"красивые"},
    {"case":"gent","number":"sing","gender":"masc","form":"красивого"},
    {"case":"gent","number":"sing","gender":"femn","form":"красивой"},
    {"case":"gent","number":"sing","gender":"neut","form":"красивого"},
    {"case":"gent","number":"plur","gender":null,"form":"красивых"}
  ]
}
```

### 🏃 8) 动词变位
- 路径: `GET /api/morph/verb-conjugation`
- 参数:
  - `word`(string, 必填): 待分析的动词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "делать",
  "language": "ru",
  "normal_form": "делать",
  "pos": "INFN",
  "cells": [
    {"tense":"pres","person":"1per","number":"sing","gender":null,"form":"делаю"},
    {"tense":"pres","person":"2per","number":"sing","gender":null,"form":"делаешь"},
    {"tense":"pres","person":"3per","number":"sing","gender":null,"form":"делает"},
    {"tense":"pres","person":"1per","number":"plur","gender":null,"form":"делаем"},
    {"tense":"pres","person":"2per","number":"plur","gender":null,"form":"делаете"},
    {"tense":"pres","person":"3per","number":"plur","gender":null,"form":"делают"},
    {"tense":"past","person":null,"number":"sing","gender":"masc","form":"делал"},
    {"tense":"past","person":null,"number":"sing","gender":"femn","form":"делала"},
    {"tense":"past","person":null,"number":"sing","gender":"neut","form":"делало"},
    {"tense":"past","person":null,"number":"plur","gender":null,"form":"делали"}
  ]
}
```

### 🔄 9) 全面变化
- 路径: `GET /api/morph/comprehensive-changes`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200: 包含名词变格、形容词变格、动词变位的完整信息

### 📊 10) 文本分析
- 路径: `POST /api/morph/text-analysis`
- 参数:
  - `text`(string, 必填): 待分析的文本
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "Привет мир",
  "language": "ru",
  "word_count": 2,
  "unique_words": 2,
  "word_analysis": [
    {
      "word": "Привет",
      "pos_tagging": {...},
      "is_known": true
    },
    {
      "word": "мир",
      "pos_tagging": {...},
      "is_known": true
    }
  ]
}
```

### 🎯 11) 词形生成
- 路径: `POST /api/morph/generate-forms`
- 参数:
  - `word`(string, 必填): 原单词
  - `target_grammemes`(array, 必填): 目标语法特征列表
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "target_grammemes": ["gent", "sing"],
  "generated_forms": [
    {
      "original_word": "друг",
      "generated_word": "друга",
      "original_tag": "NOUN,anim,masc sing,nomn",
      "generated_tag": "NOUN,anim,masc sing,gent",
      "target_grammemes": ["gent", "sing"],
      "score": 1.0,
      "error": null
    }
  ]
}
```

### ✅ 12) 语法检查
- 路径: `POST /api/morph/grammar-check`
- 参数:
  - `word`(string, 必填): 待检查的单词
  - `context_grammemes`(array, 必填): 上下文语法特征列表
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "context_grammemes": ["gent", "sing"],
  "is_grammatically_correct": true,
  "correct_parses": [...],
  "suggestions": []
}
```

### 📈 13) 数词分析
- 路径: `GET /api/morph/numeral-analysis`
- 参数:
  - `word`(string, 必填): 待分析的数词
  - `language`(string, 可选): `ru|uk`，默认 `ru`

### 📝 14) 副词分析
- 路径: `GET /api/morph/adverb-analysis`
- 参数:
  - `word`(string, 必填): 待分析的副词
  - `language`(string, 可选): `ru|uk`，默认 `ru`

### 📦 15) 批量分析
- 路径: `POST /api/morph/batch-analyze`
- 参数:
  - `words`(array, 必填): 单词列表
  - `language`(string, 可选): `ru|uk`，默认 `ru`

### 🔧 16) 基础词形分析（GET/POST）
- 路径: `GET /api/morph/analyze` 或 `POST /api/morph/analyze`
- 参数:
  - `word`(string, 必填): 待分析的单词
  - `language`(string, 可选): `ru|uk`，默认 `ru`
  - `grammemes`(string, 可选, 多值): 目标语法标签，如 `?grammemes=nomn&grammemes=sing`
  - `limit`(int, 可选): 1~32，默认 5
- 响应 200（简化示例）:
```json
{
  "input": "друг",
  "language": "ru",
  "parses": [
    {
      "normal_form": "друг",
      "tag": "NOUN,anim,masc sing,nomn",
      "score": 1.0,
      "methods_stack": ["(DictionaryAnalyzer(), 'друг', 1423, 0)"],
      "grammemes": ["NOUN","anim","masc","nomn","sing"],
      "inflected": { "word": "друг", "tag": "NOUN,anim,masc sing,nomn" }
    }
  ]
}
```

### 2) 词形分析（POST）
- 路径: `POST /api/morph/analyze`
- 请求体:
```json
{
  "word": "друг",
  "language": "ru",
  "grammemes": ["gent", "sing"],
  "limit": 5
}
```
- 响应 200（简化示例）:
```json
{
  "input": "друг",
  "language": "ru",
  "parses": [
    {
      "normal_form": "друг",
      "tag": "NOUN,anim,masc sing,nomn",
      "score": 1.0,
      "grammemes": ["NOUN","anim","masc","nomn","sing"],
      "inflected": { "word": "друга", "tag": "NOUN,anim,masc sing,gent" }
    }
  ]
}
```

### 3) 变格表（GET）
- 路径: `GET /api/morph/declension`
- 参数:
  - `word`(string, 必填)
  - `language`(string, 可选): `ru|uk`，默认 `ru`
- 响应 200:
```json
{
  "input": "друг",
  "language": "ru",
  "normal_form": "друг",
  "pos": "NOUN",
  "cells": [
    {"case":"nomn","number":"sing","gender":"masc","form":"друг"},
    {"case":"nomn","number":"plur","gender":null,"form":"друзья"},
    {"case":"gent","number":"sing","gender":"masc","form":"друга"},
    {"case":"gent","number":"plur","gender":null,"form":"друзей"},
    {"case":"datv","number":"sing","gender":"masc","form":"другу"},
    {"case":"datv","number":"plur","gender":null,"form":"друзьям"},
    {"case":"accs","number":"sing","gender":"masc","form":"друга"},
    {"case":"accs","number":"plur","gender":null,"form":"друзей"},
    {"case":"ablt","number":"sing","gender":"masc","form":"другом"},
    {"case":"ablt","number":"plur","gender":null,"form":"друзьями"},
    {"case":"loct","number":"sing","gender":"masc","form":"друге"},
    {"case":"loct","number":"plur","gender":null,"form":"друзьях"}
  ]
}
```
> 注：某些词类（如人称代词）在个别格/数上可能没有形式（返回 `form: null`）。

---

## 三、前端调用示例

### A. 使用 Fetch（浏览器/小程序 WebView/H5）

#### 🔍 智能分析（推荐）
```javascript
async function smartAnalysis(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/smart-analysis');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 📝 词性标注
```javascript
async function posTagging(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/pos-tagging');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🌳 词干词族
```javascript
async function stemLexeme(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/stem-lexeme');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### ✏️ 拼写检查
```javascript
async function spellCheck(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/spell-check');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🔍 原形查找
```javascript
async function normalForms(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/normal-forms');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 📚 名词变格
```javascript
async function getDeclension(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/declension');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 📝 形容词变格
```javascript
async function getAdjectiveDeclension(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/adjective-declension');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🏃 动词变位
```javascript
async function getVerbConjugation(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/verb-conjugation');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🔄 全面变化
```javascript
async function getComprehensiveChanges(word, language = 'ru') {
  const url = new URL('https://rubg.egg404.com/api/morph/comprehensive-changes');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 📊 文本分析
```javascript
async function analyzeText(text, language = 'ru') {
  const resp = await fetch('https://rubg.egg404.com/api/morph/text-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🎯 词形生成
```javascript
async function generateForms(word, targetGrammemes, language = 'ru') {
  const resp = await fetch('https://rubg.egg404.com/api/morph/generate-forms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, target_grammemes: targetGrammemes, language })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### ✅ 语法检查
```javascript
async function grammarCheck(word, contextGrammemes, language = 'ru') {
  const resp = await fetch('https://rubg.egg404.com/api/morph/grammar-check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, context_grammemes: contextGrammemes, language })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 📦 批量分析
```javascript
async function batchAnalyze(words, language = 'ru') {
  const resp = await fetch('https://rubg.egg404.com/api/morph/batch-analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ words, language })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

#### 🔧 基础词形分析（GET/POST）
```javascript
async function analyze(word, language = 'ru', grammemes = [], limit = 5) {
  const url = new URL('https://rubg.egg404.com/api/morph/analyze');
  url.searchParams.set('word', word);
  url.searchParams.set('language', language);
  url.searchParams.set('limit', String(limit));
  for (const g of grammemes) url.searchParams.append('grammemes', g);

  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}

async function analyzePost(word, language = 'ru', grammemes = null, limit = 5) {
  const resp = await fetch('https://rubg.egg404.com/api/morph/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ word, language, grammemes, limit })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return await resp.json();
}
```

### B. 使用 Axios（Web/React/Vue/UniApp/React Native）
```javascript
import axios from 'axios';

const api = axios.create({ baseURL: 'https://rubg.egg404.com' });

// 🔍 智能分析（推荐）
export async function smartAnalysisAxios(params) {
  return (await api.get('/api/morph/smart-analysis', { params })).data;
}

// 📝 词性标注
export async function posTaggingAxios(params) {
  return (await api.get('/api/morph/pos-tagging', { params })).data;
}

// 🌳 词干词族
export async function stemLexemeAxios(params) {
  return (await api.get('/api/morph/stem-lexeme', { params })).data;
}

// ✏️ 拼写检查
export async function spellCheckAxios(params) {
  return (await api.get('/api/morph/spell-check', { params })).data;
}

// 🔍 原形查找
export async function normalFormsAxios(params) {
  return (await api.get('/api/morph/normal-forms', { params })).data;
}

// 📚 名词变格
export async function declensionAxios(params) {
  return (await api.get('/api/morph/declension', { params })).data;
}

// 📝 形容词变格
export async function adjectiveDeclensionAxios(params) {
  return (await api.get('/api/morph/adjective-declension', { params })).data;
}

// 🏃 动词变位
export async function verbConjugationAxios(params) {
  return (await api.get('/api/morph/verb-conjugation', { params })).data;
}

// 🔄 全面变化
export async function comprehensiveChangesAxios(params) {
  return (await api.get('/api/morph/comprehensive-changes', { params })).data;
}

// 📊 文本分析
export async function textAnalysisAxios(data) {
  return (await api.post('/api/morph/text-analysis', data)).data;
}

// 🎯 词形生成
export async function generateFormsAxios(data) {
  return (await api.post('/api/morph/generate-forms', data)).data;
}

// ✅ 语法检查
export async function grammarCheckAxios(data) {
  return (await api.post('/api/morph/grammar-check', data)).data;
}

// 📦 批量分析
export async function batchAnalyzeAxios(data) {
  return (await api.post('/api/morph/batch-analyze', data)).data;
}

// 🔧 基础词形分析
export async function analyzeAxios(params) {
  return (await api.get('/api/morph/analyze', { params })).data;
}

export async function analyzePostAxios(data) {
  return (await api.post('/api/morph/analyze', data)).data;
}
```

---

## 四、错误与兼容性建议
- 若输入是拉丁字母（如 `nopa`），将被标记为 `LATN`，不会产生俄/乌变形。
- 复制粘贴可能携带“右引号”等乱码（如 `”`），若出现在 `grammemes` 参数会导致解析异常；请仅传合法标签。
- POST JSON 中请直接使用俄/乌文字，不要 URL 编码；GET 查询字符串会自动 URL 编码。
- 为增强健壮性：服务端在无法生成目标形态时返回 `form: null` 或 `inflected: null`，不再 500。

---

## 五、快速联调（cURL）

### 🔍 智能分析（推荐）
```bash
curl "https://rubg.egg404.com/api/morph/smart-analysis?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru"
```

### 📝 词性标注
```bash
curl "https://rubg.egg404.com/api/morph/pos-tagging?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru"
```

### 🌳 词干词族
```bash
curl "https://rubg.egg404.com/api/morph/stem-lexeme?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru"
```

### ✏️ 拼写检查
```bash
curl "https://rubg.egg404.com/api/morph/spell-check?word=%D0%B4%D1%80%D1%83%D0%B3%D0%B0&language=ru"
```

### 🔍 原形查找
```bash
curl "https://rubg.egg404.com/api/morph/normal-forms?word=%D0%B4%D1%80%D1%83%D0%B3%D0%B0&language=ru"
```

### 📚 名词变格
```bash
curl "https://rubg.egg404.com/api/morph/declension?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru"
```

### 📝 形容词变格
```bash
curl "https://rubg.egg404.com/api/morph/adjective-declension?word=%D0%BA%D1%80%D0%B0%D1%81%D0%B8%D0%B2%D1%8B%D0%B9&language=ru"
```

### 🏃 动词变位
```bash
curl "https://rubg.egg404.com/api/morph/verb-conjugation?word=%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C&language=ru"
```

### 🔄 全面变化
```bash
curl "https://rubg.egg404.com/api/morph/comprehensive-changes?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru"
```

### 📊 文本分析
```bash
curl -X POST "https://rubg.egg404.com/api/morph/text-analysis" \
  -H "Content-Type: application/json" \
  -d '{"text":"Привет мир","language":"ru"}'
```

### 🎯 词形生成
```bash
curl -X POST "https://rubg.egg404.com/api/morph/generate-forms" \
  -H "Content-Type: application/json" \
  -d '{"word":"друг","target_grammemes":["gent","sing"],"language":"ru"}'
```

### ✅ 语法检查
```bash
curl -X POST "https://rubg.egg404.com/api/morph/grammar-check" \
  -H "Content-Type: application/json" \
  -d '{"word":"друг","context_grammemes":["gent","sing"],"language":"ru"}'
```

### 📦 批量分析
```bash
curl -X POST "https://rubg.egg404.com/api/morph/batch-analyze" \
  -H "Content-Type: application/json" \
  -d '{"words":["друг","красивый","делать"],"language":"ru"}'
```

### 🔧 基础词形分析
```bash
# GET 词形分析
curl "https://rubg.egg404.com/api/morph/analyze?word=%D0%B4%D1%80%D1%83%D0%B3&language=ru&grammemes=nomn&grammemes=sing&grammemes=masc&limit=3"

# POST 词形分析（注意 JSON 里是原始西里尔文）
curl -X POST "https://rubg.egg404.com/api/morph/analyze" \
  -H "Content-Type: application/json" \
  -d '{"word":"друг","language":"ru","grammemes":["gent","sing"],"limit":3}'
```

---

## 六、前端展示建议（MVVM）
- **推荐使用智能分析**：一键获取所有相关信息，无需手动选择词性
- **表单项**：单词、语言、可选的语法标签（逗号分隔）、候选上限
- **结果区**：
  - 🔍 **智能分析结果**：自动展示词性标注、变格变位、词干词族等
  - 📝 **词性标注**：详细的语法特征和置信度
  - 📚 **变格变位表**：以「格 × 数」或「时态 × 人称」为二维表，空位显示 `—`
  - 🌳 **词干词族**：树状结构展示词族关系
  - ✏️ **拼写建议**：高亮显示建议词形
  - 🔍 **原形查找**：列表形式展示所有可能原形
- **交互功能**：
  - 可点击的单词链接，点击后自动重新查询
  - 响应式设计，移动端适配
- **国际化**：前端文案使用 i18n（中/英/俄/乌）
- **适配**：移动端≥360px 宽度显示单列表格；桌面端使用栅格布局

---

## 七、可扩展点（可选）
- **导出功能**：将分析结果导出为 CSV/Excel/PDF
- **批量处理**：支持一次提交多个单词批量生成分析结果
- **缓存机制**：对热门词条的分析结果进行 CDN/前端缓存
- **历史记录**：保存用户查询历史，支持快速重新查询
- **收藏功能**：允许用户收藏常用单词的分析结果
- **分享功能**：生成分享链接，方便用户分享分析结果

---

## 八、变更记录
- **2025-01-XX**: 🎉 **重大更新** - 新增智能分析功能，自动推断词性并展示所有相关词形变化
- **2025-01-XX**: 📝 新增词性标注、词干词族、拼写检查、原形查找功能
- **2025-01-XX**: 📚 新增形容词变格、动词变位、全面变化功能
- **2025-01-XX**: 📊 新增文本分析、批量分析、词形生成、语法检查功能
- **2025-01-XX**: 📈 新增数词分析、副词分析功能
- **2025-10-14**: 首版发布，新增变格表接口与健壮性处理（异常捕获，空位 `null`）
- **2025-10-14**: 适配 Python 3.12，`requirements.txt` 增加 `dawg-python`；应用启动自检 `MorphAnalyzer('ru'|'uk')` 并将异常输出到日志；控制器增加统一错误兜底，返回结构化错误码
