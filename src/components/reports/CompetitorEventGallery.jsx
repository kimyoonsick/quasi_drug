import { useState } from 'react';
import {
    NAVY, NAVY_DARK, NAVY_LIGHT, BG_LIGHT, TEXT_MAIN, TEXT_SUB, ACCENT, BORDER,
    section, sTitle,
} from './reportStyles';

/* ════════════════════════════════════════════════════════
   로컬 파일 경로 → 웹 경로 변환
   C:\Users\...\quasi_drug\data\xxx → /data/xxx
   ════════════════════════════════════════════════════════ */
function toWebPath(localPath) {
    if (!localPath) return null;
    const marker = 'quasi_drug\\data\\';
    const idx = localPath.indexOf(marker);
    if (idx === -1) return localPath;
    return '/data/' + localPath.slice(idx + marker.length).replace(/\\/g, '/');
}

/* ════════════════════════════════════════════════════════
   이미지 모달
   ════════════════════════════════════════════════════════ */
function ImageModal({ images, currentIndex, onClose, onPrev, onNext }) {
    if (!images || images.length === 0) return null;

    return (
        <div
            style={{
                position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.85)', zIndex: 10000,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer',
            }}
            onClick={onClose}
        >
            {/* 닫기 버튼 */}
            <button
                onClick={onClose}
                style={{
                    position: 'absolute', top: '1rem', right: '1.5rem',
                    background: 'none', border: 'none', color: '#fff',
                    fontSize: '2rem', cursor: 'pointer', zIndex: 10001,
                    lineHeight: 1,
                }}
            >✕</button>

            {/* 이전 */}
            {images.length > 1 && (
                <button
                    onClick={(e) => { e.stopPropagation(); onPrev(); }}
                    style={{
                        position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)',
                        background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
                        fontSize: '1.5rem', width: '3rem', height: '3rem', borderRadius: '50%',
                        cursor: 'pointer', zIndex: 10001, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                >‹</button>
            )}

            {/* 이미지 */}
            <img
                src={images[currentIndex]}
                alt=""
                onClick={(e) => e.stopPropagation()}
                style={{
                    maxWidth: '90vw', maxHeight: '90vh',
                    objectFit: 'contain', borderRadius: '0.5rem',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                    cursor: 'default',
                }}
            />

            {/* 다음 */}
            {images.length > 1 && (
                <button
                    onClick={(e) => { e.stopPropagation(); onNext(); }}
                    style={{
                        position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)',
                        background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
                        fontSize: '1.5rem', width: '3rem', height: '3rem', borderRadius: '50%',
                        cursor: 'pointer', zIndex: 10001, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                >›</button>
            )}

            {/* 페이지 인디케이터 */}
            {images.length > 1 && (
                <div style={{
                    position: 'absolute', bottom: '1.5rem',
                    color: '#fff', fontSize: '0.875rem', opacity: 0.8,
                }}>
                    {currentIndex + 1} / {images.length}
                </div>
            )}
        </div>
    );
}

/* ════════════════════════════════════════════════════════
   분류 배지 색상
   ════════════════════════════════════════════════════════ */
function getBadgeColor(type) {
    if (type === '자체') return { bg: '#e3f2fd', color: '#1565c0' };
    if (type === '제휴') return { bg: '#e8f5e9', color: '#2e7d32' };
    return { bg: '#f3e5f5', color: '#7b1fa2' };
}

/* ════════════════════════════════════════════════════════
   CompetitorEventGallery — 이벤트 카드 갤러리
   ════════════════════════════════════════════════════════ */
export default function CompetitorEventGallery({ events, competitorName, competitorColor }) {
    const [modalImages, setModalImages] = useState(null);
    const [modalIndex, setModalIndex] = useState(0);

    const openModal = (detailImages, startIdx = 0) => {
        if (!detailImages || detailImages.length === 0) return;
        setModalImages(detailImages);
        setModalIndex(startIdx);
    };

    const closeModal = () => { setModalImages(null); setModalIndex(0); };
    const prevImage = () => setModalIndex((i) => (i - 1 + modalImages.length) % modalImages.length);
    const nextImage = () => setModalIndex((i) => (i + 1) % modalImages.length);

    return (
        <div style={{ paddingTop: '0.5rem' }}>
            {/* 헤더 */}
            <section style={section}>
                <h2 style={sTitle}>
                    <span style={{ color: competitorColor || NAVY }}>{competitorName}</span> 이벤트 현황
                    <span style={{ fontSize: '0.875rem', fontWeight: 500, color: TEXT_SUB, marginLeft: '0.75rem' }}>
                        총 {events.length}건
                    </span>
                </h2>
                <div style={{ fontSize: '0.8125rem', color: TEXT_SUB, marginBottom: '1.5rem', lineHeight: 1.7 }}>
                    {competitorName}의 2026년 4월 기준 공개 이벤트 현황입니다.
                    카드를 클릭하면 상세 이미지를 확인할 수 있습니다.
                </div>

                {/* 이벤트 카드 그리드 */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                    gap: '1rem',
                }}>
                    {events.map((evt, i) => {
                        const badge = getBadgeColor(evt.type);
                        const detailImagesToShow = evt.detailImages && evt.detailImages.length > 0 
                            ? evt.detailImages 
                            : (evt.thumbnail ? [evt.thumbnail] : []);
                        const hasDetail = detailImagesToShow.length > 0;

                        return (
                            <div
                                key={i}
                                style={{
                                    border: `1px solid ${BORDER}`,
                                    borderRadius: '0.5rem',
                                    overflow: 'hidden',
                                    background: '#fff',
                                    cursor: hasDetail ? 'pointer' : 'default',
                                    transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                                    position: 'relative',
                                }}
                                onClick={() => hasDetail && openModal(detailImagesToShow)}
                                onMouseEnter={(e) => {
                                    if (hasDetail) {
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                        e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.12)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = '';
                                    e.currentTarget.style.boxShadow = '';
                                }}
                            >
                                {/* 썸네일 */}
                                <div style={{
                                    width: '100%', height: '180px',
                                    overflow: 'hidden',
                                    display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
                                    background: BG_LIGHT,
                                }}>
                                    {evt.thumbnail ? (
                                        <img
                                            src={evt.thumbnail}
                                            alt={evt.name}
                                            style={{
                                                width: '100%', height: '100%',
                                                objectFit: 'cover', objectPosition: 'top',
                                            }}
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                                e.target.parentElement.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:${TEXT_SUB};font-size:0.8rem;">이미지 없음</div>`;
                                            }}
                                        />
                                    ) : (
                                        <div style={{
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            height: '100%', color: TEXT_SUB, fontSize: '0.8rem',
                                        }}>이미지 없음</div>
                                    )}
                                </div>

                                {/* 배지 */}
                                <div style={{ position: 'absolute', top: '0.5rem', left: '0.5rem', display: 'flex', gap: '0.25rem' }}>
                                    <span style={{
                                        background: badge.bg, color: badge.color,
                                        fontSize: '0.6875rem', fontWeight: 700,
                                        padding: '0.125rem 0.5rem', borderRadius: '0.25rem',
                                    }}>{evt.type}</span>
                                    {evt.special === '특별' && (
                                        <span style={{
                                            background: '#fff3e0', color: '#e65100',
                                            fontSize: '0.6875rem', fontWeight: 700,
                                            padding: '0.125rem 0.5rem', borderRadius: '0.25rem',
                                        }}>특별</span>
                                    )}
                                </div>

                                {/* 상세 보기 아이콘 */}
                                {hasDetail && (
                                    <div style={{
                                        position: 'absolute', top: '0.5rem', right: '0.5rem',
                                        background: 'rgba(0,0,0,0.6)', color: '#fff',
                                        fontSize: '0.6875rem', padding: '0.125rem 0.5rem',
                                        borderRadius: '0.25rem', fontWeight: 600,
                                    }}>🔍 상세</div>
                                )}

                                {/* 카드 바디 */}
                                <div style={{ padding: '0.75rem' }}>
                                    <div style={{
                                        fontSize: '0.8125rem', fontWeight: 700,
                                        color: TEXT_MAIN, marginBottom: '0.375rem',
                                        lineHeight: 1.4,
                                        overflow: 'hidden', textOverflow: 'ellipsis',
                                        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                                    }}>
                                        {evt.name}
                                    </div>
                                    {evt.partner && (
                                        <div style={{
                                            fontSize: '0.6875rem', color: TEXT_SUB,
                                            marginBottom: '0.25rem',
                                        }}>
                                            제휴사: {evt.partner}
                                        </div>
                                    )}
                                    {evt.period && (
                                        <div style={{
                                            fontSize: '0.6875rem', color: TEXT_SUB,
                                        }}>
                                            📅 {evt.period}
                                        </div>
                                    )}
                                    {evt.category && (
                                        <div style={{
                                            marginTop: '0.375rem',
                                            display: 'inline-block',
                                            background: '#f0f0f0', color: TEXT_SUB,
                                            fontSize: '0.625rem', fontWeight: 600,
                                            padding: '0.125rem 0.375rem', borderRadius: '0.125rem',
                                        }}>
                                            {evt.category}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </section>

            {/* 모달 */}
            {modalImages && (
                <ImageModal
                    images={modalImages}
                    currentIndex={modalIndex}
                    onClose={closeModal}
                    onPrev={prevImage}
                    onNext={nextImage}
                />
            )}
        </div>
    );
}

/* ════════════════════════════════════════════════════════
   CSV 행을 이벤트 객체로 변환하는 유틸
   ════════════════════════════════════════════════════════ */
export function parseEventRow(row) {
    // row: [분류, 일반/특별, 제휴사, 프로모션명, 시작일, 종료일, 내용, 혜택, 카테고리, Thumbnail, Detail, URL]
    const detailRaw = row[10] || '';
    const detailImages = detailRaw
        .split('|')
        .map((p) => toWebPath(p.trim()))
        .filter(Boolean);

    const start = row[4] || '';
    const end = row[5] || '';
    const period = start && end ? `${start} ~ ${end}` : (start || end || '');

    return {
        type: row[0] || '',
        special: row[1] || '',
        partner: row[2] || '',
        name: row[3] || '',
        period,
        content: row[6] || '',
        benefit: row[7] || '',
        category: row[8] || '',
        thumbnail: row[9] || '',
        detailImages,
        url: row[11] || '',
    };
}

/* ════════════════════════════════════════════════════════
   CSV 텍스트를 파싱 (RFC4180 경량 구현)
   ════════════════════════════════════════════════════════ */
export function parseCSV(text) {
    const rows = [];
    let current = [];
    let field = '';
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (inQuotes) {
            if (ch === '"') {
                if (i + 1 < text.length && text[i + 1] === '"') {
                    field += '"';
                    i++;
                } else {
                    inQuotes = false;
                }
            } else {
                field += ch;
            }
        } else {
            if (ch === '"') {
                inQuotes = true;
            } else if (ch === ',') {
                current.push(field);
                field = '';
            } else if (ch === '\n' || ch === '\r') {
                if (ch === '\r' && i + 1 < text.length && text[i + 1] === '\n') i++;
                current.push(field);
                field = '';
                if (current.length > 1 || current[0] !== '') rows.push(current);
                current = [];
            } else {
                field += ch;
            }
        }
    }
    if (field || current.length > 0) {
        current.push(field);
        if (current.length > 1 || current[0] !== '') rows.push(current);
    }
    return rows;
}
