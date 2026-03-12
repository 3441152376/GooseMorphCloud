(function(){
  "use strict";

  /**
   * 简单 MVVM：以对象保存视图状态与动作，绑定到 DOM 事件。
   */
  const viewModel = {
    state: {
      word: "",
      language: "ru",
      grammemes: "",
      limit: 5,
    },
    setFromInputs(){
      const word = document.getElementById("word").value.trim();
      const language = document.getElementById("language").value;
      const grammemes = document.getElementById("grammemes").value.trim();
      const limit = parseInt(document.getElementById("limit").value, 10) || 5;
      this.state = { word, language, grammemes, limit };
    },
    renderResult(data){
      const el = document.getElementById("result");
      el.textContent = JSON.stringify(data, null, 2);
    },
    renderError(err){
      const el = document.getElementById("result");
      el.textContent = `请求失败: ${err?.message || String(err)}`;
      document.getElementById("declension").innerHTML = "";
    },
    renderDeclensionTable(resp){
      const root = document.getElementById("declension");
      if (!resp || !Array.isArray(resp.cells)) { root.innerHTML = ""; return; }
      const cases = ["nomn","gent","datv","accs","ablt","loct"];
      const caseName = {
        nomn:"主格", gent:"属格", datv:"与格", accs:"宾格", ablt:"工具格", loct:"前置格"
      };
      const header = `<tr><th>语法格</th><th>单数</th><th>复数</th></tr>`;
      const rows = cases.map(c => {
        const sing = resp.cells.find(x=>x.case===c && x.number==="sing");
        const plur = resp.cells.find(x=>x.case===c && x.number==="plur");
        const s1 = sing?.form ? `<span class="clickable-word" data-word="${sing.form}">${sing.form}</span>` : "—";
        const s2 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        return `<tr><td>${caseName[c]||c}</td><td>${s1}</td><td>${s2}</td></tr>`;
      }).join("");
      root.innerHTML = `<table class="declTable">${header}${rows}</table>`;
      this.bindClickableWords();
    },

    renderAdjectiveDeclensionTable(resp){
      const root = document.getElementById("declension");
      if (!resp || !Array.isArray(resp.cells)) { root.innerHTML = ""; return; }
      const cases = ["nomn","gent","datv","accs","ablt","loct"];
      const caseName = {
        nomn:"主格", gent:"属格", datv:"与格", accs:"宾格", ablt:"工具格", loct:"前置格"
      };
      const genders = ["masc","femn","neut"];
      const genderName = {masc:"阳性", femn:"阴性", neut:"中性"};
      
      let html = "<h3>形容词变格表</h3>";
      
      // 单数变格
      html += "<h4>单数</h4><table class='declTable'>";
      html += "<tr><th>语法格</th><th>阳性</th><th>阴性</th><th>中性</th></tr>";
      cases.forEach(c => {
        const masc = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="masc");
        const femn = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="femn");
        const neut = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="neut");
        const m1 = masc?.form ? `<span class="clickable-word" data-word="${masc.form}">${masc.form}</span>` : "—";
        const f1 = femn?.form ? `<span class="clickable-word" data-word="${femn.form}">${femn.form}</span>` : "—";
        const n1 = neut?.form ? `<span class="clickable-word" data-word="${neut.form}">${neut.form}</span>` : "—";
        html += `<tr><td>${caseName[c]||c}</td><td>${m1}</td><td>${f1}</td><td>${n1}</td></tr>`;
      });
      html += "</table>";
      
      // 复数变格
      html += "<h4>复数</h4><table class='declTable'>";
      html += "<tr><th>语法格</th><th>复数</th></tr>";
      cases.forEach(c => {
        const plur = resp.cells.find(x=>x.case===c && x.number==="plur");
        const p1 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        html += `<tr><td>${caseName[c]||c}</td><td>${p1}</td></tr>`;
      });
      html += "</table>";
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderVerbConjugationTable(resp){
      const root = document.getElementById("declension");
      if (!resp || !Array.isArray(resp.cells)) { root.innerHTML = ""; return; }
      
      let html = "<h3>动词变位表</h3>";
      
      // 现在时变位
      html += "<h4>现在时</h4><table class='declTable'>";
      html += "<tr><th>人称</th><th>单数</th><th>复数</th></tr>";
      const persons = ["1per","2per","3per"];
      const personName = {"1per":"第一人称", "2per":"第二人称", "3per":"第三人称"};
      persons.forEach(p => {
        const sing = resp.cells.find(x=>x.tense==="pres" && x.person===p && x.number==="sing");
        const plur = resp.cells.find(x=>x.tense==="pres" && x.person===p && x.number==="plur");
        const s1 = sing?.form ? `<span class="clickable-word" data-word="${sing.form}">${sing.form}</span>` : "—";
        const p1 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        html += `<tr><td>${personName[p]||p}</td><td>${s1}</td><td>${p1}</td></tr>`;
      });
      html += "</table>";
      
      // 过去时变位
      html += "<h4>过去时</h4><table class='declTable'>";
      html += "<tr><th>性/数</th><th>形式</th></tr>";
      const genders = ["masc","femn","neut"];
      const genderName = {masc:"阳性", femn:"阴性", neut:"中性"};
      genders.forEach(g => {
        const past = resp.cells.find(x=>x.tense==="past" && x.gender===g && x.number==="sing");
        const form = past?.form ? `<span class="clickable-word" data-word="${past.form}">${past.form}</span>` : "—";
        html += `<tr><td>${genderName[g]||g}</td><td>${form}</td></tr>`;
      });
      const pastPlur = resp.cells.find(x=>x.tense==="past" && x.number==="plur");
      const plurForm = pastPlur?.form ? `<span class="clickable-word" data-word="${pastPlur.form}">${pastPlur.form}</span>` : "—";
      html += `<tr><td>复数</td><td>${plurForm}</td></tr>`;
      html += "</table>";
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderComprehensiveChanges(resp){
      const root = document.getElementById("declension");
      let html = `<h3>${resp.input} 的全面词形变化</h3>`;
      html += `<p><strong>词性:</strong> ${resp.pos} | <strong>原形:</strong> ${resp.normal_form}</p>`;
      
      // 名词变格
      if (resp.noun_declension && resp.noun_declension.cells && resp.noun_declension.cells.length > 0) {
        html += "<h4>名词变格</h4>";
        html += this.renderDeclensionTableHtml(resp.noun_declension);
      }
      
      // 形容词变格
      if (resp.adjective_declension && resp.adjective_declension.cells && resp.adjective_declension.cells.length > 0) {
        html += "<h4>形容词变格</h4>";
        html += this.renderAdjectiveDeclensionTableHtml(resp.adjective_declension);
      }
      
      // 动词变位
      if (resp.verb_conjugation && resp.verb_conjugation.cells && resp.verb_conjugation.cells.length > 0) {
        html += "<h4>动词变位</h4>";
        html += this.renderVerbConjugationTableHtml(resp.verb_conjugation);
      }
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderDeclensionTableHtml(resp){
      const cases = ["nomn","gent","datv","accs","ablt","loct"];
      const caseName = {
        nomn:"主格", gent:"属格", datv:"与格", accs:"宾格", ablt:"工具格", loct:"前置格"
      };
      const header = `<tr><th>语法格</th><th>单数</th><th>复数</th></tr>`;
      const rows = cases.map(c => {
        const sing = resp.cells.find(x=>x.case===c && x.number==="sing");
        const plur = resp.cells.find(x=>x.case===c && x.number==="plur");
        const s1 = sing?.form ? `<span class="clickable-word" data-word="${sing.form}">${sing.form}</span>` : "—";
        const s2 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        return `<tr><td>${caseName[c]||c}</td><td>${s1}</td><td>${s2}</td></tr>`;
      }).join("");
      return `<table class="declTable">${header}${rows}</table>`;
    },

    renderAdjectiveDeclensionTableHtml(resp){
      const cases = ["nomn","gent","datv","accs","ablt","loct"];
      const caseName = {
        nomn:"主格", gent:"属格", datv:"与格", accs:"宾格", ablt:"工具格", loct:"前置格"
      };
      
      let html = "<h5>单数</h5><table class='declTable'>";
      html += "<tr><th>语法格</th><th>阳性</th><th>阴性</th><th>中性</th></tr>";
      cases.forEach(c => {
        const masc = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="masc");
        const femn = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="femn");
        const neut = resp.cells.find(x=>x.case===c && x.number==="sing" && x.gender==="neut");
        const m1 = masc?.form ? `<span class="clickable-word" data-word="${masc.form}">${masc.form}</span>` : "—";
        const f1 = femn?.form ? `<span class="clickable-word" data-word="${femn.form}">${femn.form}</span>` : "—";
        const n1 = neut?.form ? `<span class="clickable-word" data-word="${neut.form}">${neut.form}</span>` : "—";
        html += `<tr><td>${caseName[c]||c}</td><td>${m1}</td><td>${f1}</td><td>${n1}</td></tr>`;
      });
      html += "</table>";
      
      html += "<h5>复数</h5><table class='declTable'>";
      html += "<tr><th>语法格</th><th>复数</th></tr>";
      cases.forEach(c => {
        const plur = resp.cells.find(x=>x.case===c && x.number==="plur");
        const p1 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        html += `<tr><td>${caseName[c]||c}</td><td>${p1}</td></tr>`;
      });
      html += "</table>";
      
      return html;
    },

    renderVerbConjugationTableHtml(resp){
      let html = "<h5>现在时</h5><table class='declTable'>";
      html += "<tr><th>人称</th><th>单数</th><th>复数</th></tr>";
      const persons = ["1per","2per","3per"];
      const personName = {"1per":"第一人称", "2per":"第二人称", "3per":"第三人称"};
      persons.forEach(p => {
        const sing = resp.cells.find(x=>x.tense==="pres" && x.person===p && x.number==="sing");
        const plur = resp.cells.find(x=>x.tense==="pres" && x.person===p && x.number==="plur");
        const s1 = sing?.form ? `<span class="clickable-word" data-word="${sing.form}">${sing.form}</span>` : "—";
        const p1 = plur?.form ? `<span class="clickable-word" data-word="${plur.form}">${plur.form}</span>` : "—";
        html += `<tr><td>${personName[p]||p}</td><td>${s1}</td><td>${p1}</td></tr>`;
      });
      html += "</table>";
      
      html += "<h5>过去时</h5><table class='declTable'>";
      html += "<tr><th>性/数</th><th>形式</th></tr>";
      const genders = ["masc","femn","neut"];
      const genderName = {masc:"阳性", femn:"阴性", neut:"中性"};
      genders.forEach(g => {
        const past = resp.cells.find(x=>x.tense==="past" && x.gender===g && x.number==="sing");
        const form = past?.form ? `<span class="clickable-word" data-word="${past.form}">${past.form}</span>` : "—";
        html += `<tr><td>${genderName[g]||g}</td><td>${form}</td></tr>`;
      });
      const pastPlur = resp.cells.find(x=>x.tense==="past" && x.number==="plur");
      const plurForm = pastPlur?.form ? `<span class="clickable-word" data-word="${pastPlur.form}">${pastPlur.form}</span>` : "—";
      html += `<tr><td>复数</td><td>${plurForm}</td></tr>`;
      html += "</table>";
      
      return html;
    },

    renderPosTagging(resp){
      const root = document.getElementById("declension");
      if (!resp || !Array.isArray(resp.pos_tags)) { root.innerHTML = ""; return; }
      
      let html = "<h3>词性标注结果</h3>";
      html += `<p><strong>单词:</strong> ${resp.input} | <strong>是否已知:</strong> ${resp.is_known ? '是' : '否'}</p>`;
      
      resp.pos_tags.forEach((tag, index) => {
        html += `<div class="tag-info">`;
        html += `<h4>解析 ${index + 1}</h4>`;
        html += `<p><strong>词形:</strong> ${tag.word} | <strong>原形:</strong> ${tag.normal_form}</p>`;
        html += `<p><strong>词性:</strong> ${tag.pos} | <strong>标签:</strong> ${tag.tag}</p>`;
        html += `<p><strong>置信度:</strong> ${tag.score.toFixed(3)} | <strong>是否已知:</strong> ${tag.is_known ? '是' : '否'}</p>`;
        
        if (tag.case || tag.gender || tag.number || tag.person || tag.tense || tag.aspect || tag.voice || tag.mood || tag.animacy) {
          html += `<p><strong>语法特征:</strong> `;
          const features = [];
          if (tag.case) features.push(`格: ${tag.case}`);
          if (tag.gender) features.push(`性: ${tag.gender}`);
          if (tag.number) features.push(`数: ${tag.number}`);
          if (tag.person) features.push(`人称: ${tag.person}`);
          if (tag.tense) features.push(`时态: ${tag.tense}`);
          if (tag.aspect) features.push(`体: ${tag.aspect}`);
          if (tag.voice) features.push(`语态: ${tag.voice}`);
          if (tag.mood) features.push(`式: ${tag.mood}`);
          if (tag.animacy) features.push(`有生性: ${tag.animacy}`);
          html += features.join(', ') + '</p>';
        }
        
        html += `<p><strong>语法标签:</strong> ${tag.grammemes.join(', ')}</p>`;
        html += `<p><strong>西里尔标签:</strong> ${tag.cyr_grammemes.join(', ')}</p>`;
        html += `</div>`;
      });
      
      root.innerHTML = html;
    },

    renderSpellCheck(resp){
      const root = document.getElementById("declension");
      if (!resp) { root.innerHTML = ""; return; }
      
      let html = "<h3>拼写检查结果</h3>";
      html += `<p><strong>单词:</strong> ${resp.input}</p>`;
      html += `<p><strong>是否已知:</strong> ${resp.is_known ? '是' : '否'}</p>`;
      
      if (resp.suggestions && resp.suggestions.length > 0) {
        html += "<h4>建议词形:</h4><ul>";
        resp.suggestions.forEach(suggestion => {
          html += `<li><span class="clickable-word" data-word="${suggestion.word}">${suggestion.word}</span> (${suggestion.normal_form}) - ${suggestion.tag} (${suggestion.score.toFixed(3)})</li>`;
        });
        html += "</ul>";
      } else if (!resp.is_known) {
        html += "<p>未找到相似词形建议</p>";
      }
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderNormalForms(resp){
      const root = document.getElementById("declension");
      if (!resp) { root.innerHTML = ""; return; }
      
      let html = "<h3>原形查找结果</h3>";
      html += `<p><strong>单词:</strong> ${resp.input}</p>`;
      html += `<p><strong>原形数量:</strong> ${resp.count}</p>`;
      
      if (resp.normal_forms && resp.normal_forms.length > 0) {
        html += "<h4>可能的原形:</h4><ul>";
        resp.normal_forms.forEach(form => {
          html += `<li><span class="clickable-word" data-word="${form}">${form}</span></li>`;
        });
        html += "</ul>";
      } else {
        html += "<p>未找到原形</p>";
      }
      
      if (resp.error) {
        html += `<p class="error">错误: ${resp.error}</p>`;
      }
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderStemLexeme(resp){
      const root = document.getElementById("declension");
      if (!resp) { root.innerHTML = ""; return; }
      
      let html = "<h3>词干和词族分析</h3>";
      html += `<p><strong>单词:</strong> ${resp.input}</p>`;
      
      if (resp.stems && resp.stems.length > 0) {
        html += "<h4>词干信息:</h4><ul>";
        resp.stems.forEach(stem => {
          html += `<li><strong>词干:</strong> <span class="clickable-word" data-word="${stem.stem}">${stem.stem}</span> (${stem.pos}) - 置信度: ${stem.score.toFixed(3)}</li>`;
        });
        html += "</ul>";
      }
      
      if (resp.lexemes && resp.lexemes.length > 0) {
        html += "<h4>词族信息:</h4>";
        resp.lexemes.forEach(lexeme => {
          html += `<div class="lexeme-info">`;
          html += `<h5>${lexeme.word} (共 ${lexeme.total_forms} 个词形)</h5>`;
          html += "<ul>";
          lexeme.lexeme_forms.forEach(form => {
            html += `<li><span class="clickable-word" data-word="${form.word}">${form.word}</span> - ${form.tag}</li>`;
          });
          html += "</ul></div>";
        });
      }
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    renderSmartAnalysis(resp){
      const root = document.getElementById("declension");
      if (!resp || !resp.analysis) { root.innerHTML = ""; return; }
      
      let html = "<h3>🔍 智能分析结果</h3>";
      html += `<div class="smart-summary">`;
      html += `<p><strong>单词:</strong> ${resp.input} | <strong>主要词性:</strong> ${resp.primary_pos} | <strong>置信度:</strong> ${(resp.confidence * 100).toFixed(1)}%</p>`;
      html += `<p><strong>是否已知:</strong> ${resp.is_known ? '是' : '否'}</p>`;
      html += `</div>`;
      
      // 词性标注
      if (resp.analysis.pos_tagging && resp.analysis.pos_tagging.pos_tags && resp.analysis.pos_tagging.pos_tags.length > 0) {
        html += "<h4>📝 词性标注</h4>";
        html += `<div class="tag-info">`;
        resp.analysis.pos_tagging.pos_tags.forEach((tag, index) => {
          html += `<div class="tag-item">`;
          html += `<p><strong>解析 ${index + 1}:</strong> ${tag.word} → ${tag.normal_form} (${tag.pos})</p>`;
          html += `<p><strong>标签:</strong> ${tag.tag} | <strong>置信度:</strong> ${tag.score.toFixed(3)}</p>`;
          if (tag.case || tag.gender || tag.number || tag.person || tag.tense || tag.aspect || tag.voice || tag.mood || tag.animacy) {
            const features = [];
            if (tag.case) features.push(`格: ${tag.case}`);
            if (tag.gender) features.push(`性: ${tag.gender}`);
            if (tag.number) features.push(`数: ${tag.number}`);
            if (tag.person) features.push(`人称: ${tag.person}`);
            if (tag.tense) features.push(`时态: ${tag.tense}`);
            if (tag.aspect) features.push(`体: ${tag.aspect}`);
            if (tag.voice) features.push(`语态: ${tag.voice}`);
            if (tag.mood) features.push(`式: ${tag.mood}`);
            if (tag.animacy) features.push(`有生性: ${tag.animacy}`);
            html += `<p><strong>语法特征:</strong> ${features.join(', ')}</p>`;
          }
          html += `</div>`;
        });
        html += `</div>`;
      }
      
      // 词形变化
      if (resp.analysis.comprehensive_changes) {
        const changes = resp.analysis.comprehensive_changes;
        
        // 名词变格
        if (changes.noun_declension && changes.noun_declension.cells && changes.noun_declension.cells.length > 0) {
          html += "<h4>📚 名词变格</h4>";
          html += this.renderDeclensionTableHtml(changes.noun_declension);
        }
        
        // 形容词变格
        if (changes.adjective_declension && changes.adjective_declension.cells && changes.adjective_declension.cells.length > 0) {
          html += "<h4>📝 形容词变格</h4>";
          html += this.renderAdjectiveDeclensionTableHtml(changes.adjective_declension);
        }
        
        // 动词变位
        if (changes.verb_conjugation && changes.verb_conjugation.cells && changes.verb_conjugation.cells.length > 0) {
          html += "<h4>🏃 动词变位</h4>";
          html += this.renderVerbConjugationTableHtml(changes.verb_conjugation);
        }
      }
      
      // 词干词族
      if (resp.analysis.stem_lexeme && (resp.analysis.stem_lexeme.stems.length > 0 || resp.analysis.stem_lexeme.lexemes.length > 0)) {
        html += "<h4>🌳 词干词族</h4>";
        if (resp.analysis.stem_lexeme.stems && resp.analysis.stem_lexeme.stems.length > 0) {
          html += "<h5>词干信息:</h5><ul>";
          resp.analysis.stem_lexeme.stems.forEach(stem => {
            html += `<li><strong>词干:</strong> <span class="clickable-word" data-word="${stem.stem}">${stem.stem}</span> (${stem.pos}) - 置信度: ${stem.score.toFixed(3)}</li>`;
          });
          html += "</ul>";
        }
        
        if (resp.analysis.stem_lexeme.lexemes && resp.analysis.stem_lexeme.lexemes.length > 0) {
          html += "<h5>词族信息:</h5>";
          resp.analysis.stem_lexeme.lexemes.forEach(lexeme => {
            html += `<div class="lexeme-info">`;
            html += `<h6>${lexeme.word} (共 ${lexeme.total_forms} 个词形)</h6>`;
            html += "<ul>";
            lexeme.lexeme_forms.forEach(form => {
              html += `<li><span class="clickable-word" data-word="${form.word}">${form.word}</span> - ${form.tag}</li>`;
            });
            html += "</ul></div>";
          });
        }
      }
      
      // 原形查找
      if (resp.analysis.normal_forms && resp.analysis.normal_forms.normal_forms && resp.analysis.normal_forms.normal_forms.length > 0) {
        html += "<h4>🔍 原形查找</h4>";
        html += `<p><strong>原形数量:</strong> ${resp.analysis.normal_forms.count}</p>`;
        html += "<ul>";
        resp.analysis.normal_forms.normal_forms.forEach(form => {
          html += `<li><span class="clickable-word" data-word="${form}">${form}</span></li>`;
        });
        html += "</ul>";
      }
      
      // 拼写检查
      if (resp.analysis.spell_check) {
        const spell = resp.analysis.spell_check;
        if (!spell.is_known && spell.suggestions && spell.suggestions.length > 0) {
          html += "<h4>✏️ 拼写建议</h4>";
          html += "<ul>";
          spell.suggestions.forEach(suggestion => {
            html += `<li><span class="clickable-word" data-word="${suggestion.word}">${suggestion.word}</span> (${suggestion.normal_form}) - ${suggestion.tag} (${suggestion.score.toFixed(3)})</li>`;
          });
          html += "</ul>";
        }
      }
      
      root.innerHTML = html;
      this.bindClickableWords();
    },

    bindClickableWords(){
      document.querySelectorAll('.clickable-word').forEach(el => {
        el.addEventListener('click', (e) => {
          const word = e.target.dataset.word;
          if (word) {
            document.getElementById('word').value = word;
            this.fetchSmartAnalysis(); // 使用智能分析重新查询
          }
        });
      });
    },

    async fetchGet(){
      this.setFromInputs();
      const { word, language, grammemes, limit } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      if (grammemes) {
        for (const g of grammemes.split(",").map(s => s.trim()).filter(Boolean)) {
          params.append("grammemes", g);
        }
      }
      params.set("limit", String(limit));
      const url = `/api/morph/analyze?${params.toString()}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      document.getElementById("declension").innerHTML = "";
    },
    async fetchPost(){
      this.setFromInputs();
      const { word, language, grammemes, limit } = this.state;
      const payload = {
        word,
        language,
        grammemes: grammemes ? grammemes.split(",").map(s => s.trim()).filter(Boolean) : null,
        limit,
      };
      const resp = await fetch("/api/morph/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      document.getElementById("declension").innerHTML = "";
    },
    async fetchDeclension(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/declension?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderDeclensionTable(json);
    },

    async fetchAdjectiveDeclension(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/adjective-declension?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderAdjectiveDeclensionTable(json);
    },

    async fetchVerbConjugation(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/verb-conjugation?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderVerbConjugationTable(json);
    },

    async fetchComprehensive(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/comprehensive-changes?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderComprehensiveChanges(json);
    },

    async fetchPosTagging(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/pos-tagging?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderPosTagging(json);
    },

    async fetchSpellCheck(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/spell-check?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderSpellCheck(json);
    },

    async fetchNormalForms(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/normal-forms?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderNormalForms(json);
    },

    async fetchStemLexeme(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/stem-lexeme?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderStemLexeme(json);
    },

    async fetchSmartAnalysis(){
      this.setFromInputs();
      const { word, language } = this.state;
      const params = new URLSearchParams();
      params.set("word", word);
      params.set("language", language);
      const resp = await fetch(`/api/morph/smart-analysis?${params.toString()}`);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      const json = await resp.json();
      this.renderResult(json);
      this.renderSmartAnalysis(json);
    },
  };

  document.getElementById("btnGet").addEventListener("click", () => {
    viewModel.fetchGet().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnPost").addEventListener("click", () => {
    viewModel.fetchPost().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnDecl").addEventListener("click", () => {
    viewModel.fetchDeclension().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnAdjDecl").addEventListener("click", () => {
    viewModel.fetchAdjectiveDeclension().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnVerbConj").addEventListener("click", () => {
    viewModel.fetchVerbConjugation().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnComprehensive").addEventListener("click", () => {
    viewModel.fetchComprehensive().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnPosTagging").addEventListener("click", () => {
    viewModel.fetchPosTagging().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnSpellCheck").addEventListener("click", () => {
    viewModel.fetchSpellCheck().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnNormalForms").addEventListener("click", () => {
    viewModel.fetchNormalForms().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnStemLexeme").addEventListener("click", () => {
    viewModel.fetchStemLexeme().catch(err => viewModel.renderError(err));
  });
  document.getElementById("btnSmartAnalysis").addEventListener("click", () => {
    viewModel.fetchSmartAnalysis().catch(err => viewModel.renderError(err));
  });
})();
