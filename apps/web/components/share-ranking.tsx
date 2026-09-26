"use client";

export function ShareRanking({ resultId, entityName }: { resultId: string | null; entityName: string }) {
  if (!resultId) return null;
  const imagePath = `/api/share/${resultId}?format=square`;
  const share = async () => {
    const url = window.location.href;
    if (navigator.share) {
      await navigator.share({ title: `${entityName} on TopTenUG`, text: `See ${entityName}'s official TopTenUG ranking.`, url });
      return;
    }
    await navigator.clipboard.writeText(url);
  };
  return <div className="share-actions">
    <button type="button" className="share-button" onClick={share}>Share</button>
    <a className="share-button" href={`${imagePath}&download=1`}>Download card</a>
  </div>;
}
