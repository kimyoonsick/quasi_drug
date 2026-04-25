import { useState, useEffect } from 'react';
import ReportLayout from '../common/ReportLayout';
import { EditableField } from '../common/EditableField';
import {
    NAVY, NAVY_DARK, NAVY_LIGHT, BLUE, GREEN, BG_LIGHT, TEXT_MAIN, TEXT_SUB, ACCENT, BORDER,
    section, sTitle, tbl, thStyle, thR, thC, tdStyle, tdR, tdC, tdBold,
    zebraRow, execSummaryGrad, execLabel,
    kpiCard, kpiLabel, kpiValue, kpiSub, kpiGrid,
    callout, subHeading, sourceSection, sourceLabel, sourceList,
} from './reportStyles';
import CompetitorEventGallery, { parseCSV, parseEventRow } from './CompetitorEventGallery';

/* ═══ CSV 파일 경로 ═══ */
const CSV_MAP = {
    baropharm: '/data/2604_baropharm.csv',
    hmp: '/data/2604_hmp.csv',
    platpharm: '/data/2604_platpharm.csv',
    saeropharm: '/data/2604_saeropharm.csv',
};

/* ═══ 탭 정의 ═══ */
const TABS = [
    { key: 'summary', label: '요약' },
    { key: 'baropharm', label: '바로팜', color: '#1565c0' },
    { key: 'hmp', label: 'HMP몰', color: '#2e7d32' },
    { key: 'platpharm', label: '플랫팜', color: '#7b1fa2' },
    { key: 'saeropharm', label: '새로팜', color: '#e65100' },
];

/* ═══ 요약 데이터 (기존) ═══ */
const SCALE_DATA = [
    { name: '바로팜', total: 63, self: 25, partner: 31, etc: 5, special: 2 },
    { name: 'HMP몰', total: 30, self: 1, partner: 29, etc: 0, special: 0 },
    { name: '새로팜', total: 53, self: 1, partner: 52, etc: 0, special: 0 },
    { name: '플랫팜', total: 12, self: 1, partner: 11, etc: 0, special: 0 },
];
const SCALE_TOTAL = { total: 158, self: 28, partner: 123, etc: 5, special: 2 };

const MATRIX_DATA = [
    { type: '입점업체 월간 사은품', baro: 18, hmp: 24, saero: 30, plat: 2, note: '전 플랫폼 공통 최다 — 도매상 제휴 기본 운영' },
    { type: '쿠폰/구매혜택 이벤트', baro: 0, hmp: 0, saero: 18, plat: 1, note: '새로팜(쿠폰 더블 18사·업체별 1건), 플랫팜(계좌이체 1.5% 할인)' },
    { type: '카드/간편결제 프로모션', baro: 8, hmp: 0, saero: 4, plat: 3, note: '바로팜(BC·우리·KB국민·네이버페이 등), 새로팜(롯데·하나·KB Pay)' },
    { type: '자사 서비스/기능 홍보', baro: 10, hmp: 0, saero: 0, plat: 1, note: '바로팜 최다 — BPCS·팜페이지·연동몰·함께배송 등' },
    { type: '브랜드관/제약사 협업', baro: 10, hmp: 1, saero: 0, plat: 4, note: '바로팜 이건뭐약 시리즈, 플랫팜 종근당 2건·보고신약' },
    { type: '커뮤니티/참여형', baro: 5, hmp: 0, saero: 0, plat: 1, note: '바로팜(지식왕·댓글·무엇이든 물어보살), 플랫팜(퀴즈)' },
    { type: '게이미피케이션/라이브', baro: 3, hmp: 0, saero: 0, plat: 0, note: '바로팜 단독 — 봄인해제·라이브커머스·필렌즈 챌린지' },
    { type: '멤버십/온보딩', baro: 4, hmp: 0, saero: 1, plat: 1, note: '바로팜(신규웰컴·멤버십유지), 새로팜(멤버십개편)' },
    { type: '기술/학술 기반', baro: 1, hmp: 0, saero: 0, plat: 2, note: '플랫팜(더이로운 AI헬스체커·종근당 위고비심포지엄)' },
    { type: '금융 제휴', baro: 0, hmp: 0, saero: 0, plat: 1, note: '플랫팜(경남은행 BNK 메디칼론)' },
    { type: '기타(당첨자발표 등)', baro: 4, hmp: 5, saero: 0, plat: 0, note: '—' },
];

const TREND_DATA = [
    { no: 1, trend: '카드/간편결제 필수화', detail: '3사 이상이 카드·간편결제 제휴 운영, 미운영 시 경쟁력 열위', who: '바로팜·새로팜·플랫팜' },
    { no: 2, trend: '입점업체 월간 이벤트 표준화', detail: '도매상별 월 1회 사은품 증정이 업계 표준으로 정착', who: '바로팜·HMP몰' },
    { no: 3, trend: '게이미피케이션 선도', detail: '수집형 미션·룰렛 등 바로팜만 유일하게 운영, 타사 미도입', who: '바로팜' },
    { no: 4, trend: '라이브커머스 도입', detail: '바로팜이 제약사 협업 라이브 방송 진행, B2B에서도 시도', who: '바로팜' },
    { no: 5, trend: '기술/학술 기반 차별화', detail: 'AI 헬스체커·심포지엄 등 비가격 경쟁 요소 부상', who: '플랫팜' },
    { no: 6, trend: '금융 제휴 확장', detail: '약국 전용 대출(메디칼론)·카드 신규발급까지 확장', who: '플랫팜·새로팜' },
    { no: 7, trend: '커뮤니티 생태계 구축', detail: '약사 지식인·댓글·전문가 상담 등 비거래 활동 유도', who: '바로팜' },
];

const ACTION_DATA = [
    { priority: '1순위', area: '입점업체 월간 이벤트', level: '바로팜 18건·HMP 24건·새로팜 30건/월', action: '주요 도매상 입점 후 월간 사은품 이벤트 표준 운영 체계 구축' },
    { priority: '1순위', area: '카드/결제 제휴', level: '3사 이상 평균 3~8건', action: '최소 2개 카드사 + 1개 간편결제 제휴 확보' },
    { priority: '2순위', area: '구매 연동 쿠폰', level: '새로팜 구간별 쿠폰', action: '구매금액 구간별 쿠폰(10/20/30만원) 도입으로 객단가 상승' },
    { priority: '2순위', area: '제약사 협업', level: '바로팜 이건뭐약·플랫팜 종근당 시리즈', action: '퀴즈·셀링가이드 작성 등 제약사 공동 프로모션 기획' },
    { priority: '3순위', area: '게이미피케이션', level: '바로팜만 운영', action: '자사 IP 기반 미션형 이벤트 중장기 로드맵 수립' },
    { priority: '3순위', area: '커뮤니티 활성화', level: '바로팜만 운영', action: '약사 Q&A·리뷰·댓글 포인트 적립 체계 설계' },
];

/* ═══ 탭 버튼 스타일 ═══ */
const tabBar = {
    display: 'flex', gap: '0.5rem', flexWrap: 'wrap',
    marginBottom: '1.5rem', padding: '0.75rem 1rem',
    background: `linear-gradient(135deg, ${NAVY_DARK} 0%, ${NAVY} 100%)`,
    borderRadius: '0.75rem',
    position: 'sticky', top: 0, zIndex: 100,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
};
const tabBtn = (active) => ({
    padding: '0.5rem 1.25rem',
    border: active ? '2px solid #fff' : '1px solid rgba(255,255,255,0.3)',
    borderRadius: '2rem',
    background: active ? 'rgba(255,255,255,0.2)' : 'transparent',
    color: '#fff',
    fontWeight: active ? 700 : 500,
    fontSize: '0.875rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backdropFilter: active ? 'blur(4px)' : 'none',
});

/* ═══ 메인 보고서 ═══ */
export default function CompetitorDashboardReport({ titleOverride }) {
    const [activeTab, setActiveTab] = useState('summary');
    const [eventsCache, setEventsCache] = useState({});
    const [loading, setLoading] = useState(false);

    /* CSV fetch & parse */
    useEffect(() => {
        if (activeTab === 'summary' || eventsCache[activeTab]) return;
        setLoading(true);
        fetch(CSV_MAP[activeTab])
            .then((r) => r.text())
            .then((text) => {
                const rows = parseCSV(text);
                // skip header row
                let events = rows.slice(1).filter(r => r.length >= 4 && r[3]).map(parseEventRow);

                if (activeTab === 'baropharm') {
                    events = events.map(evt => ({
                        ...evt,
                        detailImages: evt.detailImages && evt.detailImages.length > 0 ? evt.detailImages.slice(1) : evt.detailImages
                    }));
                } else if (activeTab === 'hmp') {
                    events = events.map(evt => ({
                        ...evt,
                        detailImages: evt.detailImages && evt.detailImages.length > 2 ? evt.detailImages.slice(3) : evt.detailImages
                    }));
                }

                setEventsCache((prev) => ({ ...prev, [activeTab]: events }));
            })
            .catch((err) => {
                console.error('CSV load error:', err);
                setEventsCache((prev) => ({ ...prev, [activeTab]: [] }));
            })
            .finally(() => setLoading(false));
    }, [activeTab]);

    const barColor = (val, max) => {
        const ratio = val / max;
        if (ratio >= 0.7) return GREEN;
        if (ratio >= 0.3) return BLUE;
        return NAVY_LIGHT;
    };

    const currentTabMeta = TABS.find((t) => t.key === activeTab);

    return (
        <ReportLayout
            type="분석 보고서"
            title="[경쟁사] 4월 이벤트 분석"
            subtitle="바로팜·HMP몰·새로팜·플랫팜"
            date="2026.04.22"
            version="v1.3"
            audience="마케팅팀"
            titleOverride={titleOverride}
        >
            <div className="report-tab-content" style={{ paddingTop: '1rem' }}>

                {/* ═══ 탭 바 ═══ */}
                <div style={tabBar}>
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            style={tabBtn(activeTab === tab.key)}
                            onClick={() => setActiveTab(tab.key)}
                            onMouseEnter={(e) => { if (activeTab !== tab.key) e.target.style.background = 'rgba(255,255,255,0.1)'; }}
                            onMouseLeave={(e) => { if (activeTab !== tab.key) e.target.style.background = 'transparent'; }}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* ═══ 요약 탭 ═══ */}
                {activeTab === 'summary' && (
                    <>
                        {/* Executive Summary */}
                        <section style={section}>
                            <div style={execSummaryGrad}>
                                <div style={execLabel}>EXECUTIVE SUMMARY</div>
                                <ul style={{ margin: 0, paddingLeft: '1.25rem', listStyle: 'disc', lineHeight: 2 }}>
                                    <li><strong>바로팜</strong> 63건, <strong>HMP몰</strong> 30건, <strong>새로팜</strong> 53건, <strong>플랫팜</strong> 12건 — 총 <strong>158건</strong>의 진행 중 이벤트를 수집·분석 (기준일: 2026.04.22)</li>
                                    <li>제휴 이벤트가 전체의 <strong>78%</strong> — 입점업체(도매상) 월간 사은품 증정이 업계 공통 표준으로 정착</li>
                                    <li>바로팜만 유일하게 <strong>게이미피케이션</strong>(봄인해제), <strong>라이브커머스</strong>, <strong>커뮤니티 참여형</strong> 이벤트를 운영하며 플랫폼 체류시간 확대 전략 차별화</li>
                                    <li>플랫팜은 <strong>AI 헬스체커</strong>(더이로운 협업)·<strong>종근당 심포지엄·퀴즈</strong> 등 기술·학술 기반 이벤트로 차별화 시도</li>
                                </ul>
                            </div>
                        </section>

                        {/* 1. 규모 비교 */}
                        <section style={section}>
                            <h2 style={sTitle}><EditableField id="CDR_sTitle_scale" fallback="1. 경쟁사별 이벤트 규모 비교" /></h2>
                            <div style={{ ...kpiGrid, gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
                                {SCALE_DATA.map((d, i) => (
                                    <div key={i} style={kpiCard}>
                                        <div style={kpiLabel}>{d.name}</div>
                                        <div style={{ ...kpiValue, color: barColor(d.total, 63) }}>{d.total}건</div>
                                        <div style={kpiSub}>자체 {d.self} · 제휴 {d.partner}</div>
                                    </div>
                                ))}
                            </div>
                            <table style={tbl}>
                                <thead>
                                    <tr>
                                        <th style={{ ...thStyle, width: '100px' }}>경쟁사</th>
                                        <th style={thC}>총 이벤트</th>
                                        <th style={thC}>자체</th>
                                        <th style={thC}>제휴</th>
                                        <th style={thC}>기타/미분류</th>
                                        <th style={thC}>특별</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {SCALE_DATA.map((d, i) => (
                                        <tr key={i} style={zebraRow(i)}>
                                            <td style={{ ...tdStyle, fontWeight: 700 }}>{d.name}</td>
                                            <td style={{ ...tdC, fontWeight: 700, color: barColor(d.total, 63) }}>{d.total}</td>
                                            <td style={tdC}>{d.self}</td>
                                            <td style={tdC}>{d.partner}</td>
                                            <td style={tdC}>{d.etc}</td>
                                            <td style={tdC}>{d.special}</td>
                                        </tr>
                                    ))}
                                    <tr style={{ background: NAVY_DARK }}>
                                        <td style={{ ...tdStyle, fontWeight: 700, color: '#fff' }}>합계</td>
                                        <td style={{ ...tdC, fontWeight: 700, color: '#fff' }}>{SCALE_TOTAL.total}</td>
                                        <td style={{ ...tdC, color: '#fff' }}>{SCALE_TOTAL.self}</td>
                                        <td style={{ ...tdC, color: '#fff' }}>{SCALE_TOTAL.partner}</td>
                                        <td style={{ ...tdC, color: '#fff' }}>{SCALE_TOTAL.etc}</td>
                                        <td style={{ ...tdC, color: '#fff' }}>{SCALE_TOTAL.special}</td>
                                    </tr>
                                </tbody>
                            </table>
                            <div style={{ fontSize: '0.75rem', color: TEXT_SUB, marginTop: '0.5rem', lineHeight: 1.7 }}>
                                * 새로팜은 업체별 개별 이벤트 기준 카운트 적용 — 쿠폰 더블 18사 · 외품 이벤트 15사 · 외품 쿠폰 모음 15사 → 48건 + 비벤더 5건 = 53건
                            </div>
                        </section>

                        {/* 2. 매트릭스 */}
                        <section style={section}>
                            <h2 style={sTitle}><EditableField id="CDR_sTitle_matrix" fallback="2. 이벤트 유형별 분류 매트릭스" /></h2>
                            <table style={tbl}>
                                <thead>
                                    <tr>
                                        <th style={{ ...thStyle, width: '180px' }}>유형</th>
                                        <th style={thC}>바로팜</th>
                                        <th style={thC}>HMP몰</th>
                                        <th style={thC}>새로팜</th>
                                        <th style={thC}>플랫팜</th>
                                        <th style={thStyle}>비고</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {MATRIX_DATA.map((row, i) => {
                                        const max = Math.max(row.baro, row.hmp, row.saero, row.plat);
                                        const hl = (v) => v === max && max > 0 ? { fontWeight: 700, color: GREEN } : {};
                                        return (
                                            <tr key={i} style={zebraRow(i)}>
                                                <td style={{ ...tdStyle, fontWeight: 600 }}>{row.type}</td>
                                                <td style={{ ...tdC, ...hl(row.baro) }}>{row.baro}건</td>
                                                <td style={{ ...tdC, ...hl(row.hmp) }}>{row.hmp}건</td>
                                                <td style={{ ...tdC, ...hl(row.saero) }}>{row.saero}건</td>
                                                <td style={{ ...tdC, ...hl(row.plat) }}>{row.plat}건</td>
                                                <td style={{ ...tdStyle, color: TEXT_SUB }}>{row.note}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                            <div style={{ ...callout, marginTop: '1rem' }}>
                                <strong>데이터 인사이트:</strong> 새로팜은 노출 이벤트(8건) 대비 업체별 실 참여 이벤트(53건)의 괴리가 크며, 다수 도매상을 하나의 기획전에 번들로 묶어 운영하는 구조임. HMP몰·바로팜은 도매상별 개별 페이지 방식으로 운영해 이벤트 수가 더 높게 집계됨 — 단순 건수 비교보다 <strong>운영 방식(번들형 vs. 개별형)</strong>의 차이로 해석해야 함.
                            </div>
                        </section>

                        {/* 3. 트렌드 */}
                        <section style={section}>
                            <h2 style={sTitle}><EditableField id="CDR_sTitle_trend" fallback="3. 트렌드 및 인사이트" /></h2>
                            <h3 style={subHeading}>트렌드 요약</h3>
                            <table style={tbl}>
                                <thead>
                                    <tr>
                                        <th style={{ ...thC, width: '40px' }}>#</th>
                                        <th style={{ ...thStyle, width: '180px' }}>트렌드</th>
                                        <th style={thStyle}>상세</th>
                                        <th style={{ ...thStyle, width: '150px' }}>관련 경쟁사</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {TREND_DATA.map((row, i) => (
                                        <tr key={i} style={zebraRow(i)}>
                                            <td style={{ ...tdC, fontWeight: 700, color: NAVY }}>{row.no}</td>
                                            <td style={{ ...tdStyle, fontWeight: 600 }}>{row.trend}</td>
                                            <td style={tdStyle}>{row.detail}</td>
                                            <td style={{ ...tdStyle, color: TEXT_SUB }}>{row.who}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            <h3 style={{ ...subHeading, marginTop: '1.5rem' }}>피코몰 대비 시사점 (액션 아이템)</h3>
                            <div style={{ fontSize: '0.8125rem', color: TEXT_SUB, marginBottom: '1rem', lineHeight: 1.7 }}>
                                경쟁사 분석을 바탕으로 피코몰에 우선순위별로 적용할 마케팅 액션 아이템입니다.
                            </div>
                            <table style={tbl}>
                                <thead>
                                    <tr>
                                        <th style={{ ...thC, width: '80px' }}>우선순위</th>
                                        <th style={{ ...thStyle, width: '140px' }}>영역</th>
                                        <th style={thStyle}>현 경쟁사 수준</th>
                                        <th style={thStyle}>피코몰 액션 아이템</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ACTION_DATA.map((row, i) => (
                                        <tr key={i} style={zebraRow(i)}>
                                            <td style={{
                                                ...tdC, fontWeight: 700,
                                                color: row.priority === '1순위' ? ACCENT : row.priority === '2순위' ? NAVY : TEXT_SUB,
                                            }}>{row.priority}</td>
                                            <td style={{ ...tdStyle, fontWeight: 600 }}>{row.area}</td>
                                            <td style={{ ...tdStyle, color: TEXT_SUB }}>{row.level}</td>
                                            <td style={tdStyle}>{row.action}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div style={{ ...callout, marginTop: '1rem' }}>
                                <strong>차별화 포인트:</strong> 경쟁사 대부분이 도매상 사은품·카드 제휴의 <strong>가격 경쟁</strong>에 집중하는 반면, 피코몰은 <strong>약국 경영에 실질적으로 필요한 실무 혜택</strong>(샘플·실무 도구·포인트)과 <strong>커뮤니티 기반 참여형 이벤트</strong>를 결합하여 체류시간과 재구매율을 동시에 높이는 방향으로 설계해야 합니다.
                            </div>
                        </section>

                        {/* 출처 */}
                        <div style={sourceSection}>
                            <div style={sourceLabel}>DATA SOURCES</div>
                            <ul style={sourceList}>
                                <li>[외부] 바로팜 (baropharm.com) 이벤트 페이지 — 2026.04.21 크롤링 (63건)</li>
                                <li>[외부] HMP몰 (hmpmall.co.kr) 이벤트 페이지 — 2026.04.21 크롤링 (30건)</li>
                                <li>[외부] 새로팜 (saeropharm.com) 이벤트 페이지 — 2026.04.21 크롤링 (8건 노출 / 업체별 53건)</li>
                                <li>[외부] 플랫팜 (platpharm.co.kr) 이벤트 페이지 — 2026.04.21 크롤링 (12건)</li>
                            </ul>
                        </div>
                        <div style={{ fontSize: '11px', color: TEXT_SUB, textAlign: 'right', marginTop: '1rem' }}>
                            * 본 분석은 각 플랫폼 공개 이벤트 페이지 기준이며, 비공개 프로모션 및 앱 전용 이벤트는 포함되지 않을 수 있습니다.
                        </div>
                    </>
                )}

                {/* ═══ 경쟁사 이벤트 탭 ═══ */}
                {activeTab !== 'summary' && (
                    loading ? (
                        <section style={section}>
                            <div style={{ textAlign: 'center', padding: '3rem', color: TEXT_SUB }}>
                                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>⏳</div>
                                이벤트 데이터를 불러오는 중...
                            </div>
                        </section>
                    ) : eventsCache[activeTab] ? (
                        <CompetitorEventGallery
                            events={eventsCache[activeTab]}
                            competitorName={currentTabMeta.label}
                            competitorColor={currentTabMeta.color}
                        />
                    ) : (
                        <section style={section}>
                            <div style={{ textAlign: 'center', padding: '3rem', color: TEXT_SUB }}>
                                데이터를 불러올 수 없습니다.
                            </div>
                        </section>
                    )
                )}

            </div>
        </ReportLayout>
    );
}
