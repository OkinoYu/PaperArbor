import base64
import copy
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from common import CATEGORIES, atomic_write, site_path, validate_records
from build_index import render_index
from validate_site import Document, data_image, validate, validate_article
from render_article import render, prepare_body
from embed_images import embed
from fetch_sources import parse_atom, parse_abs, fetch, lookup
from radar import discover
from publish_entry import publish

SVG='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>test</title><circle cx="5" cy="5" r="2"/></svg>'
ATOM='''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2409.12191v2</id><title> Test paper </title><author><name>A Author</name></author><published>2024-09-18T00:00:00Z</published><updated>2024-10-03T00:00:00Z</updated><summary>Evidence here.</summary></entry></feed>'''.encode()

def record():
 return dict(id='test-2409.12191',title='测试论文',summary='Mechanism',category='VLM',type='Single',published='2024-09-18',added='2026-10-10',path='examples/VLM/test.html',tags=['test'],sources=[dict(id='2409.12191v2',title='Test',authors='A Author',url='https://arxiv.org/abs/2409.12191v2',version='v2',published='2024-09-18')],evidence='data/evidence/test.json')

class PipelineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
  for name in ('templates','assets'):shutil.copytree(ROOT/name,self.root/name)
  for name in ('examples/VLM','data/evidence','drafts'):(self.root/name).mkdir(parents=True,exist_ok=True)
  atomic_write(self.root/'data/papers.json','[]\n');atomic_write(self.root/'index.html',render_index([],self.root))
  self.entry=record();self.article=self.root/'drafts/article.html';self.evidence=self.root/'drafts/evidence.json'
  self.article.write_text(render('<h2 id="method">方法</h2><p>Evidence</p>','测试','scope','VLM','Single',self.root))
  self.evidence.write_text(json.dumps({'claims':[dict(anchor='method',source='2409.12191v2',locator='Section 2',statement='Evidence')]}))
 def tearDown(self):self.tmp.cleanup()
 def go(self,**kw):return publish(self.root,self.entry,self.article,self.evidence,**kw)
 def test_publish_updates_whole_catalog(self):
  self.assertTrue(self.go()['ok']);self.assertTrue(validate(self.root)['ok']);self.assertEqual(len(json.loads((self.root/'data/papers.json').read_text())),1)
 def test_dry_run_does_not_publish(self):
  before=(self.root/'index.html').read_bytes();self.assertTrue(self.go(dry_run=True)['ok']);self.assertEqual(before,(self.root/'index.html').read_bytes());self.assertFalse((self.root/self.entry['path']).exists());self.assertFalse((self.root/'.publish.lock').exists())
 def test_repeated_publish_refuses(self):
  self.go();old=(self.root/self.entry['path']).read_bytes()
  with self.assertRaises(ValueError):self.go()
  self.assertEqual(old,(self.root/self.entry['path']).read_bytes())
 def test_replace_preserves_paths(self):
  self.go();self.entry['path']='examples/VLM/other.html'
  with self.assertRaises(ValueError):self.go(replace=True)
 def test_intended_revision(self):
  self.go();self.article.write_text(self.article.read_text().replace('Evidence','Revised evidence'));self.assertTrue(self.go(replace=True)['ok']);self.assertIn('Revised',(self.root/self.entry['path']).read_text())
 def prepare_move(self):
  self.go();old=self.entry['path'];self.entry.update(category='OPD',path='examples/OPD/test.html',aliases=[old]);return old
 def test_category_move_keeps_identity_and_updates_navigation(self):
  self.go();old=self.entry['path'];original_evidence=(self.root/self.entry['evidence']).read_bytes()
  other=copy.deepcopy(self.entry);other.update(id='related',type='Series',path='examples/VLM/related.html',evidence='data/evidence/related.json')
  linked=self.root/'drafts/linked.html';linked.write_text(render('<h2 id="method">Related</h2><a href="test.html?view=reader#method">old</a><a href="https://example.org/test.html#method">external</a>','Related','scope','VLM','Series',self.root))
  publish(self.root,other,linked,self.evidence)
  self.entry.update(category='OPD',path='examples/OPD/test.html',aliases=[old])
  self.assertTrue(self.go(replace=True,move=True)['ok'])
  result=json.loads((self.root/'data/papers.json').read_text());moved=next(r for r in result if r['id']==self.entry['id'])
  self.assertEqual(moved['added'],'2026-10-10');self.assertEqual(moved['evidence'],self.entry['evidence']);self.assertEqual(original_evidence,(self.root/self.entry['evidence']).read_bytes())
  alias=Document((self.root/old).read_text(),True);self.assertEqual(alias.redirect_target,'../OPD/test.html')
  links=Document((self.root/other['path']).read_text(),True).links
  self.assertIn('../OPD/test.html?view=reader#method',links);self.assertIn('https://example.org/test.html#method',links)
  self.assertTrue(validate(self.root)['ok']);self.assertEqual(len(result),2)
 def test_move_requires_explicit_flag_and_old_alias(self):
  self.prepare_move()
  with self.assertRaises(ValueError):self.go(replace=True)
  self.entry['aliases']=[]
  with self.assertRaises(ValueError):self.go(replace=True,move=True)
 def test_move_dry_run_changes_nothing(self):
  self.prepare_move();before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.assertTrue(self.go(replace=True,move=True,dry_run=True)['ok'])
  self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_move_refuses_destination_collision(self):
  self.prepare_move();dest=self.root/self.entry['path'];dest.parent.mkdir();dest.write_text('keep')
  with self.assertRaises(ValueError):self.go(replace=True,move=True)
  self.assertEqual(dest.read_text(),'keep')
 def test_move_rolls_back_redirect_and_new_article(self):
  import publish_entry
  old=self.prepare_move();before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};original=publish_entry.atomic_write;failed=False
  def fail_after_redirect(path,text):
   nonlocal failed
   original(path,text)
   if path==self.root/old and not failed:failed=True;raise OSError('failure after redirect write')
  with patch.object(publish_entry,'atomic_write',side_effect=fail_after_redirect):
   with self.assertRaises(OSError):self.go(replace=True,move=True)
  self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_alias_contract_and_collision(self):
  for alias in ('../outside.html',self.entry['path'],'examples/Unknown/x.html'):
   r=copy.deepcopy(self.entry);r['aliases']=[alias]
   with self.assertRaises(ValueError):validate_records([r],self.root,False)
  r=copy.deepcopy(self.entry);r['aliases']=['examples/OPD/test.html'];other=copy.deepcopy(r);other.update(id='other',type='Series',category='OPD',path=r['aliases'][0],aliases=[])
  with self.assertRaises(ValueError):validate_records([r,other],self.root,False)
 def test_redirect_target_must_match_catalog(self):
  old=self.prepare_move();self.go(replace=True,move=True);p=self.root/old;p.write_text(p.read_text().replace('../OPD/test.html','../../index.html'))
  self.assertTrue(any('redirect must target' in e for e in validate(self.root)['errors']))
 def test_category_count_follows_supported_directions(self):
  text=render_index([],self.root)
  self.assertIn('data-category="OPD"',text);self.assertIn(f'<strong>{len(CATEGORIES)}</strong> 个研究方向',text)
 def test_invalid_candidate_leaves_site_unchanged(self):
  self.article.write_text(self.article.read_text().replace('</main>','<img src="https://example.org/x.png" alt="external"></main>'))
  before=(self.root/'index.html').read_bytes()
  with self.assertRaises(ValueError):self.go()
  self.assertEqual(before,(self.root/'index.html').read_bytes());self.assertFalse((self.root/self.entry['path']).exists())
 def test_commit_exception_rolls_back(self):
  import publish_entry
  original=publish_entry.atomic_write;calls=0
  def fail_once(path,text):
   nonlocal calls
   if path.is_relative_to(self.root):
    calls+=1
    if calls==3:raise OSError('simulated disk failure')
   return original(path,text)
  before=(self.root/'index.html').read_bytes()
  with patch.object(publish_entry,'atomic_write',side_effect=fail_once):
   with self.assertRaises(OSError):self.go()
  self.assertFalse((self.root/self.entry['path']).exists());self.assertFalse((self.root/self.entry['evidence']).exists());self.assertEqual(before,(self.root/'index.html').read_bytes());self.assertEqual([],json.loads((self.root/'data/papers.json').read_text()))
 def test_lock_refuses_concurrent_publish(self):
  (self.root/'.publish.lock').write_text('other process')
  with self.assertRaises(FileExistsError):self.go()
  self.assertEqual('other process',(self.root/'.publish.lock').read_text())
 def test_duplicate_canonical_sources(self):
  second=copy.deepcopy(self.entry);second['id']='other';second['path']='examples/VLM/other.html';second['sources'][0]['id']='2409.12191v1'
  with self.assertRaises(ValueError):validate_records([self.entry,second],self.root,False)
 def test_different_modes_may_share_paper(self):
  second=copy.deepcopy(self.entry);second['id']='other';second['path']='examples/VLM/other.html';second['type']='Series';validate_records([self.entry,second],self.root,False)
 def test_case_insensitive_duplicate_path(self):
  second=copy.deepcopy(self.entry);second['id']='other';second['type']='Series';second['path']='examples/VLM/TEST.html'
  with self.assertRaises(ValueError):validate_records([self.entry,second],self.root,False)
 def test_path_escape_and_symlink(self):
  for p in ('../secret','/absolute','https://a.test/x','examples/../secret','examples\\x','examples/x#fragment'):
   with self.assertRaises(ValueError):site_path(self.root,p)
  (self.root/'out').symlink_to('/private/tmp')
  with self.assertRaises(ValueError):site_path(self.root,'out/secret')
 def test_dates_and_categories(self):
  for key,value in [('published','2026-02-30'),('category','Unknown'),('type','Unknown'),('tags',[])]:
   r=copy.deepcopy(self.entry);r[key]=value
   with self.assertRaises(ValueError):validate_records([r],self.root,False)
 def test_json_injection_and_html_escape(self):
  r=copy.deepcopy(self.entry);r['title']='</script><img src=x>';s=render_index([r],self.root)
  self.assertIn('&lt;/script&gt;',s);payload=s.split('<script id="papers-data" type="application/json">')[1].split('</script>')[0];self.assertNotIn('<',payload);self.assertEqual(json.loads(payload)[0]['title'],r['title'])
 def test_stale_index_detected(self):
  self.go();(self.root/'index.html').write_text('stale');self.assertFalse(validate(self.root)['ok'])
 def test_broken_cross_file_anchor(self):
  self.go();p=self.root/self.entry['path'];p.write_text(p.read_text().replace('</main>','<a href="../../index.html#missing">bad</a></main>'));self.assertTrue(any('broken anchor' in e for e in validate(self.root)['errors']))
 def test_root_absolute_link_fails(self):
  self.article.write_text(self.article.read_text().replace('</main>','<a href="/index.html">bad</a></main>'))
  with self.assertRaises(ValueError):self.go()
 def test_missing_evidence_anchor_fails(self):
  self.evidence.write_text(self.evidence.read_text().replace('method','nonexistent'))
  with self.assertRaises(ValueError):self.go()
 def test_unregistered_article_fails(self):
  (self.root/'examples/VLM/orphan.html').write_text(self.article.read_text());self.assertFalse(validate(self.root)['ok'])
 def test_standalone_dependency_and_unquoted_image(self):
  base=self.article.read_text()
  for extra in ('<script src="https://cdn.test/x.js"></script>','<img src=x.png alt="x">','<style>x{background:url(https://a.test/x)}</style>','<source srcset="x.png 1x">'):
   self.assertTrue(Document(base.replace('</main>',extra+'</main>'),True).errors)
 def test_url_constructor_is_not_css_asset(self):
  text=self.article.read_text().replace('</body>','<script>const target=new URL("https://example.org");</script></body>')
  self.assertFalse(Document(text,True).errors)
 def test_svg_paint_server_cannot_load_remote_asset(self):
  bad=SVG.replace('<circle','<circle fill="url(https://example.org/paint.svg#x)"')
  self.assertFalse(data_image('data:image/svg+xml;base64,'+base64.b64encode(bad.encode()).decode()))
  extra='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" role="img" aria-labelledby="paint"><title id="paint">Paint</title><rect fill="url(https://example.org/x.svg#x)"/></svg>'
  self.assertTrue(Document(self.article.read_text().replace('</main>',extra+'</main>'),True).errors)
 def test_invalid_math_svg_duplicate_ids(self):
  extra='<h2 id="method">duplicate</h2><svg viewBox="0 0 1 1" role="img" aria-labelledby="s"><title id="s">bad</title><g></svg><math aria-label="bad"><mfrac><mi>x</mi></math>'
  self.assertTrue(Document(self.article.read_text().replace('</main>',extra+'</main>'),True).errors)
 def test_embedded_svg_and_markers_survive_transform(self):
  (self.root/'drafts/x.svg').write_text(SVG)
  text='<img src="x.svg" alt="test"><svg><path marker-end="url(#arrow)"/></svg>'
  result=embed(text,self.root/'drafts');self.assertIn('marker-end="url(#arrow)"',result);self.assertIn('data:image/svg+xml;base64,',result)
 def test_embed_idempotent_and_css_attribute_quotes(self):
  (self.root/'drafts/x.svg').write_text(SVG)
  result=embed('<div style="background:url(x.svg)"></div>',self.root/'drafts');self.assertNotIn('url("',result);self.assertEqual(result,embed(result,self.root/'drafts'))
 def test_embedded_svg_cannot_hide_external_assets(self):
  bad=SVG.replace('</svg>','<image href="https://a.test/x.png"/></svg>')
  self.assertFalse(data_image('data:image/svg+xml;base64,'+base64.b64encode(bad.encode()).decode()))
 def test_accessibility_label_target_required(self):
  extra='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" role="img" aria-labelledby="missing"><title>Test</title></svg>'
  self.assertTrue(Document(self.article.read_text().replace('</main>',extra+'</main>'),True).errors)
 def test_data_image_rejects_mime_mismatch(self):
  self.assertFalse(data_image('data:image/png;base64,'+base64.b64encode(b'not png').decode()));self.assertFalse(data_image('data:image/png;base64,@@'))
 def test_renderer_requires_heading_ids(self):
  with self.assertRaises(ValueError):render('<h2>No id</h2>','x','x','VLM','Single',self.root)
 def test_atom_keeps_version_and_dates(self):
  item=parse_atom(ATOM)[0];self.assertEqual(item['id'],'2409.12191v2');self.assertEqual(item['published'],'2024-09-18');self.assertEqual(item['authors'],'A Author');self.assertEqual(item['pdf_url'],'https://arxiv.org/pdf/2409.12191v2')
 def test_arxiv_url_lookup(self):
  with patch('fetch_sources.http',return_value=ATOM) as get:
   self.assertEqual(lookup('https://arxiv.org/pdf/2409.12191v2')['id'],'2409.12191v2');self.assertIn('id_list=2409.12191v2',get.call_args[0][0])
 def test_api_identity_mismatch_refused(self):
  with patch('fetch_sources.http',return_value=ATOM):
   with self.assertRaises(ValueError):lookup('2308.12966')
 def test_primary_abs_fallback_pins_version(self):
  html=b'<meta name="citation_arxiv_id" content="2409.12191"><meta name="citation_title" content="Test"><meta name="citation_author" content="Author"><meta name="citation_date" content="2024/09/18"><meta name="citation_online_date" content="2024/10/03"><meta name="citation_abstract" content="Abstract"><strong>[v2]</strong>'
  with patch('fetch_sources.http',side_effect=[OSError('429'),html]):
   result=lookup('2409.12191v2')
  self.assertEqual(result['version'],'v2');self.assertIn('API unavailable',result['retrieval_note'])
  with self.assertRaises(ValueError):parse_abs(html,'2409.12191v1')
 def test_api_error_feed_is_failure(self):
  with self.assertRaises(ValueError):parse_atom(b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/api/errors</id><title>Error</title><summary>Invalid query</summary></entry></feed>')
 def test_ambiguous_title_not_silently_selected(self):
  data=ATOM.replace(b'</feed>',ATOM.split(b'<entry>')[1].split(b'</entry>')[0].join([b'<entry>',b'</entry></feed>']))
  with patch('fetch_sources.http',return_value=data):
   with self.assertRaises(ValueError):lookup('Ambiguous')
 def test_local_pdf_cache_preserves_hash_and_refuses_overwrite(self):
  source=self.root/'paper.pdf';source.write_bytes(b'%PDF-1.4\ntest fixture')
  item=fetch(str(source),self.root/'cache');self.assertEqual(item['status'],'local-unverified');self.assertTrue(item['sha256'])
  with self.assertRaises(FileExistsError):fetch(str(source),self.root/'cache')
 def test_radar_failure_retains_status(self):
  with patch('radar.http',side_effect=OSError('offline')):result=discover('all:vlm',date(2024,9,1),date(2024,9,30))
  self.assertEqual(result['sources'][0]['status'],'failed');self.assertEqual(result['candidates'],[])
 def test_radar_bounded_and_limit_disclosed(self):
  with patch('radar.http',return_value=ATOM):result=discover('all:vlm',date(2024,9,1),date(2024,9,30),1)
  self.assertTrue(result['sources'][0]['possibly_truncated']);self.assertEqual(len(result['candidates']),1)
  with patch('radar.http',return_value=ATOM):result=discover('all:vlm',date(2024,10,1),date(2024,10,30))
  self.assertEqual([],result['candidates'])
 def evidenced(self, body='<h2 id="method">方法</h2><h3>内部变换</h3><p>Evidence</p>', **kwargs):
  ledger=json.loads(self.evidence.read_text())
  return render(body,'测试','scope','VLM','Single',self.root,entry=self.entry,ledger=ledger,**kwargs)
 def test_portable_evidence_survives_move(self):
  self.article.write_text(self.evidenced(standalone=True))
  with tempfile.TemporaryDirectory() as td:
   moved=Path(td)/'copied.html';shutil.copyfile(self.article,moved)
   self.assertTrue(validate_article(moved)['ok'])
   self.assertNotIn('../../',moved.read_text())
 def test_standalone_requires_embedded_evidence(self):
  self.assertFalse(validate_article(self.article)['ok'])
 def test_standalone_rejects_file_link(self):
  self.article.write_text(self.evidenced(standalone=True).replace('</main>','<a href="other.html">bad</a></main>'))
  self.assertTrue(any('file dependency' in error for error in validate_article(self.article)['errors']))
 def test_safe_embedded_claim_and_static_fallback(self):
  ledger=json.loads(self.evidence.read_text());ledger['claims'][0]['statement']='</script><img src=x> & 机制'
  self.evidence.write_text(json.dumps(ledger));self.article.write_text(self.evidenced(standalone=True))
  doc=Document(self.article.read_text(),True)
  self.assertEqual(doc.evidence_payload['ledger'],ledger);self.assertFalse(doc.errors)
  self.assertIn('&lt;/script&gt;',self.article.read_text());self.assertIn('返回对应正文',self.article.read_text())
 def test_stale_embedded_evidence_blocks_publication(self):
  self.article.write_text(self.evidenced());self.go()
  before=(self.root/self.entry['path']).read_bytes()
  ledger=json.loads(self.evidence.read_text());ledger['claims'][0]['statement']='Changed';self.evidence.write_text(json.dumps(ledger))
  with self.assertRaises(ValueError):self.go(replace=True)
  self.assertEqual(before,(self.root/self.entry['path']).read_bytes())
 def test_embedded_sources_cannot_use_unsafe_url(self):
  self.entry['sources'][0]['url']='javascript:alert(1)'
  with self.assertRaises(ValueError):self.evidenced(standalone=True)
 def test_evidence_kind_is_checked(self):
  ledger=json.loads(self.evidence.read_text());ledger['claims'][0]['kind']='fabricated';self.evidence.write_text(json.dumps(ledger))
  with self.assertRaises(ValueError):self.evidenced()
 def test_evidence_and_entry_must_be_paired(self):
  with self.assertRaises(ValueError):render('<h2 id="method">方法</h2>','x','x','VLM','Single',self.root,entry=self.entry)
 def test_revision_preserves_added_date(self):
  self.go();self.entry['added']='2026-10-11'
  with self.assertRaises(ValueError):self.go(replace=True)
 def test_heading_ids_stable_and_collision_safe(self):
  body='<h2 id="method">方法</h2><h3 id="method-part-1">指定</h3><h3>自动</h3>'
  normalized=prepare_body(body)
  self.assertIn('id="method-part-2"',normalized);self.assertEqual(normalized,prepare_body(normalized))
  for extra in ('<p id="method">重复</p>','<p id="evidence-data">冲突</p>','<h1>重复主标题</h1>'):
   with self.assertRaises(ValueError):self.evidenced(body+extra)
 def test_related_reading_explains_actual_overlap(self):
  other=copy.deepcopy(self.entry);other.update(id='related',path='examples/VLM/related.html',title='相关')
  unrelated=copy.deepcopy(other);unrelated.update(id='unrelated',title='无关',tags=['none']);unrelated['sources'][0]['id']='2308.12966v1'
  result=self.evidenced(records=[self.entry,other,unrelated])
  self.assertIn('共同原始来源',result);self.assertIn('../../examples/VLM/related.html',result);self.assertNotIn('无关',result)
  self.assertNotIn('<aside class="related-reading"',self.evidenced(standalone=True,records=[other]))
 def test_metadata_checks_updated_hash_and_body(self):
  for changes in ({'updated':'2026-10-09'},{'updated':'bad'},{'body':'../outside.html'},{'body':'data/body.html'}):
   entry=copy.deepcopy(self.entry);entry.update(changes)
   with self.assertRaises(ValueError):validate_records([entry],self.root,False)
  entry=copy.deepcopy(self.entry);entry['sources'][0]['sha256']='bad'
  with self.assertRaises(ValueError):validate_records([entry],self.root,False)
 def test_direct_pdf_links_remain_direct(self):
  self.entry['sources'][0]['pdf_url']='https://arxiv.org/pdf/2409.12191v2'
  result=self.evidenced('<h2 id="method">方法</h2><a href="https://arxiv.org/pdf/2409.12191v2#page=4">PDF</a><a href="https://arxiv.org/abs/2409.12191v2">来源</a>')
  self.assertIn('v2#page=4">PDF',result);self.assertIn('data-source="2409.12191v2">来源',result)
 def test_authored_body_checked_in_publish_candidate(self):
  self.entry['body']='articles/test/body.html'
  with self.assertRaises(ValueError):self.go(dry_run=True)
  body=self.root/self.entry['body'];body.parent.mkdir(parents=True);body.write_text('<h2 id="method">方法</h2>')
  self.assertTrue(self.go(dry_run=True)['ok']);self.assertFalse((self.root/self.entry['path']).exists())
 def test_live_repository_is_consistent(self):self.assertTrue(validate(ROOT)['ok'])

if __name__=='__main__':unittest.main()
