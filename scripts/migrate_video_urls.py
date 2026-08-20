"""
One-shot migration: update all saved analysis JSON files to use the new
/api/analyses/{id}/video endpoint URL instead of the old /storage/annotated_videos/ path.
"""
import json
from pathlib import Path

analyses_dir = Path('storage/analyses')
updated = 0
skipped = 0

for json_file in analyses_dir.glob('*.json'):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        old_url = data.get('annotated_video_url', '')
        analysis_id = data.get('analysis_id', json_file.stem)

        # Only update if using old /storage/ path
        if old_url and '/storage/annotated_videos/' in old_url:
            data['annotated_video_url'] = f'/api/analyses/{analysis_id}/video'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f'Updated: {json_file.name}  {old_url} -> {data["annotated_video_url"]}')
            updated += 1
        else:
            skipped += 1

    except Exception as e:
        print(f'ERROR {json_file.name}: {e}')

print(f'\nDone. Updated {updated}, skipped {skipped}.')
